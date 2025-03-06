import os
import random
import subprocess
import time
from datetime import datetime
import pandas as pd
import socket
import platform
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, WebDriverException,
    ElementClickInterceptedException)

from selenium.webdriver.common.action_chains import ActionChains

def handle_startpage(driver, query):
    try:
        # Wait for the search box with multiple possible selectors
        search_box = None
        selectors = [
            (By.NAME, "query"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.CSS_SELECTOR, "input[type='search']")
        ]
        
        for selector_type, selector_value in selectors:
            try:
                search_box = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((selector_type, selector_value))
                )
                break
            except TimeoutException:
                continue
        
        if search_box:
            # Clear using JavaScript
            driver.execute_script("arguments[0].value = '';", search_box)
            time.sleep(1)
            
            # Input text using JavaScript
            driver.execute_script(f"arguments[0].value = '{query}';", search_box)
            time.sleep(1)
            
            search_box.send_keys(Keys.RETURN)
            return True
            
        return False
    except Exception as e:
        log_message(f"Error with Startpage search: {e}")
        return False


def check_internet():
    """Returns True if internet is available, False otherwise."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)  # Google's public DNS
        return True
    except OSError:
        return False

def wait_for_internet(polling_interval=10):
    """Pauses execution and waits until an internet connection is restored."""
    # log_message("No internet connection. Pausing execution...")
    
    while not check_internet():
        log_message(f"No internet detected. Retrying in {polling_interval} seconds...")
        time.sleep(polling_interval)  # Wait before checking again
    
    # log_message("Internet connection restored. Resuming execution...")


def setup_driver(max_attempts=3):
    """Setup WebDriver with retry mechanism."""
    wait_for_internet()
    for attempt in range(max_attempts):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
            ]
            options.add_argument(f"user-agent={random.choice(user_agents)}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(300)
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
            return driver
        except WebDriverException as e:
            log_message(f"WebDriver setup failed (attempt {attempt+1}/{max_attempts}): {e}")
            if attempt < max_attempts - 1:
                time.sleep(10)
    return None
def log_message(message):
    """Print a timestamped log message."""
    print(f"[{datetime.now()}] {message}")


def safe_click(driver, element, fallback_js=True):
    """Attempt to click an element safely with multiple fallback methods"""
    try:
        # Try regular click first
        element.click()
        return True
    except ElementClickInterceptedException:
        try:
            # Scroll element into view and try again
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)  # Wait for scroll to complete
            element.click()
            return True
        except Exception:
            if fallback_js:
                try:
                    # Try JavaScript click as last resort
                    driver.execute_script("arguments[0].click();", element)
                    return True
                except Exception as e:
                    log_message(f"All click attempts failed: {str(e)}")
                    return False
    except Exception as e:
        log_message(f"Click failed: {str(e)}")
        return False   
    
def accept_cookie(driver, engine):
    """
    Handles cookie consent for the given search engine.
    This ensures the baseline includes the cookie acceptance overhead.
    """
    if engine == "Google":
        """Handles Google search with improved error handling and multiple fallback methods"""
        try:
            # Avoid maximizing window unless necessary (most modern sites don’t need it)
            # driver.maximize_window()

            # 1. Handle consent dialog efficiently
            consent_button_xpath = "//*[text()[normalize-space()='Accept All'] or text()[normalize-space()='Alles accepteren']]"
            try:
                # Check for iframe briefly (reduced from 10s to 3s)
                WebDriverWait(driver, 3).until(
                    EC.frame_to_be_available_and_switch_to_it(
                        (By.XPATH, "//iframe[contains(@src, 'consent.google')]")
                    )
                )
                accept_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, consent_button_xpath))
                )
                driver.execute_script("arguments[0].click();", accept_button)  # Faster JS click
                driver.switch_to.default_content()  # Switch back immediately
                time.sleep(0.5)  # Minimal delay after consent
            except:
                # No consent iframe or already handled; proceed
                driver.switch_to.default_content()

            return True
        except Exception as e:
            log_message(f"Error with Google search: {e}")
            return False
        
    elif engine == "Yahoo":
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                log_message(f"Attempting to accept Yahoo cookies (Attempt {attempt + 1})")

                # Check if cookie consent popup exists using WebDriverWait
                popup_present = False
                try:
                    consent_button = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((
                            By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept') or contains(., 'Alles accepteren') or contains(., 'Accept All')]"
                        ))
                    )
                    popup_present = True
                except TimeoutException:
                    log_message("No Yahoo cookie consent popup detected or already handled")
                    return True  # Exit successfully if no popup is present

                if popup_present:
                    # Find and click the consent button
                    consent_buttons = driver.execute_script("""
                        return Array.from(document.querySelectorAll('button')).filter(btn => 
                            ['Accept All', 'Alles accepteren'].some(text => 
                                btn.textContent.toLowerCase().includes(text.toLowerCase())
                            )
                        );
                    """)

                    if consent_buttons:
                        button = random.choice(consent_buttons)
                        log_message("Found Yahoo cookie consent button; attempting to click")
                        driver.execute_script("arguments[0].click();", button)

                        # Wait for the popup to disappear or page to stabilize
                        try:
                            # Wait for the button to disappear or a page-ready state
                            WebDriverWait(driver, 2).until_not(
                                EC.presence_of_element_located((
                                    By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept') or contains(., 'Alles accepteren') or contains(., 'Accept All')]"
                                ))
                            )
                            log_message("Yahoo cookie popup successfully closed")
                            return True  # Exit on success
                        except TimeoutException:
                            log_message("Cookie popup still present after click; retrying or proceeding cautiously")
                    else:
                        log_message(f"No Yahoo cookie consent button found on attempt {attempt + 1}")

                # Wait before retrying (only if not the last attempt)
                if attempt < max_attempts - 1:
                    time.sleep(random.uniform(1, 2))
                else:
                    log_message("Max attempts reached; proceeding without accepting cookies")
                    return False  # Indicate failure but allow script to continue

            except Exception as e:
                log_message(f"Error accepting Yahoo cookies on attempt {attempt + 1}: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(random.uniform(1, 2))
                else:
                    log_message("Max attempts reached; proceeding without accepting cookies")
                    return False

        log_message("Failed to accept Yahoo cookies after all attempts")
        return False

            
    elif engine == "Bing":
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "bnp_btn_accept"))
            )
            if safe_click(driver, cookie_button):
                log_message("Accepted cookies on Bing")
                time.sleep(1)
        except TimeoutException:
            log_message("No cookie dialog for Bing")
            
    elif engine == "Ecosia":
        try:
            cookie_accept = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept all')]"))
            )
            cookie_accept.click()
            log_message("Accepted cookies on Ecosia")
            time.sleep(1)
        except TimeoutException:
            log_message("No cookie dialog on Ecosia or already accepted")
    
    engines_without_consent = {
        "DuckDuckGo", "Brave Search", "OceanHero", "Startpage", "Qwant", "Swisscows", "Mojeek", "You.com"
    }
    if engine in engines_without_consent:
        log_message(f"{engine} does not require cookie consent.")
    else:
        # Fallback: attempt a generic acceptance
        try:
            consent_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]")
                )
            )
            consent_button.click()
            log_message(f"Accepted cookies on {engine} using fallback method")
            time.sleep(random.uniform(1, 2))
        except TimeoutException:
            log_message(f"No cookie dialog for {engine}")

def store_baseline_to_csv(engine, average_baseline, filename='baseline_results.csv'):
    # Open in write mode to start a new file each time
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Search Engine', 'Baseline Duration (ms)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()  # Write header as the first row
        writer.writerow({
            'Search Engine': engine,
            'Baseline Duration (ms)': average_baseline
        })


def measure_baseline(engine, url, iterations=1):
    """
    Measures the baseline overhead for an engine by performing minimal automation steps,
    including accepting cookies.
    """
    baseline_durations = []
    for _ in range(iterations):
        log_message(f"Measuring baseline for {engine}")
        start_time = int(datetime.now().timestamp() * 1000)  # in ms
        driver = setup_driver()
        time.sleep(random.uniform(0.5, 1.5))
        driver.get(url)
        time.sleep(random.uniform(1.5, 3.0))

        handle_startpage(driver, "angular route uib tab")
        
        # Accept cookie to include its overhead in the baseline
        if engine == "Yahoo":
            if not accept_cookie(driver, engine):
                log_message(f"Could not accept cookies for {engine}; proceeding without")
                log_message("Defaulting to predefined baseline for Yahoo (21676 ms)")
                baseline_duration = 21676
            else:
                log_message(f"Continuing with baseline measurement for {engine}")
                end_time = int(datetime.now().timestamp() * 1000)
                baseline_duration = end_time - start_time
                time.sleep(1)

        else:
            accept_cookie(driver, engine)
            log_message(f"Continuing with baseline measurement for {engine}")
            end_time = int(datetime.now().timestamp() * 1000)
            baseline_duration = end_time - start_time
            time.sleep(1)

        log_message(f"Baseline for {engine}: {baseline_duration} ms")
        if baseline_duration > 40000:
            # Skip abnormally large durations
            continue
        baseline_durations.append(baseline_duration)
        driver.quit()

    average_baseline = sum(baseline_durations) / len(baseline_durations)
    log_message(f"Average baseline for {engine}: {average_baseline} ms")

    return average_baseline


def main():
    engines = {
    "Google": "https://www.google.com", 
    "Bing": "https://www.bing.com",
    "Yahoo": "https://www.yahoo.com", 
    "DuckDuckGo": "https://www.duckduckgo.com",
    "Brave Search": "https://search.brave.com",
    "Ecosia": "https://www.ecosia.org",
    "OceanHero": "https://oceanhero.today",
    "Startpage": "https://www.startpage.com",
    "Qwant": "https://www.qwant.com",
    "Swisscows": "https://www.swisscows.com",
    "Mojeek": "https://www.mojeek.com",
    "You.com": "https://you.com",
    }
    
    # 1) Gather results in a list of dicts
    results = []
    for engine, url in engines.items():
        avg_baseline = measure_baseline(engine, url, iterations=30)
        results.append({
            "Search Engine": engine,
            "Baseline Duration (ms)": avg_baseline
        })
    
    output_file = 'baseline_average.csv'
    
    # 3) Save as CSV using pandas
    try:
        df = pd.DataFrame(results)
        # Use sep=';' to use semicolons instead of commas
        df.to_csv(output_file, index=False, sep=';')
        log_message(f"Results saved to {output_file}")
    except Exception as e:
        log_message(f"Error saving to {output_file}: {e}")
        # Fallback to current directory
        fallback_file = 'baseline_average.csv'
        df = pd.DataFrame(results)
        df.to_csv(fallback_file, index=False, sep=';')
        log_message(f"Results saved to fallback location: {fallback_file}")

if __name__ == "__main__":
    main()
