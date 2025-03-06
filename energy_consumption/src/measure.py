import os
import random
import subprocess
import time
from datetime import datetime
import pandas as pd
import socket
import platform
import socket
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, WebDriverException,
    ElementClickInterceptedException)

from selenium.webdriver.common.action_chains import ActionChains

# Search Engines
SEARCH_ENGINES = {
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

SEARCH_QUERIES = [
    "angular route uib tab",
    # "react setstate sub property",
    # "bootstrap button next to input",
    # "forcelayout api",
    # "golang copy built in",
    # "strlen",
    # "java comparator interface",
    # "ubuntu search packages",
    # "URI uri = new URIBuilder",
    # "java throw exception example",
    # "mdn transform origin",
    # "segmented circle css",
    # "show is not a member of org.apache.spark.sql.GroupedData",
    # "babel-jest can't console log in babel jest",
    # "json minify"
]

DEFAULT_DURATION = 60 #60 # Search test duration in seconds
DEFAULT_WARMUP = 300 #300  # Warmup duration in seconds (should be 300 for real tests)
OUTPUT_FILE = "search_engine_results/search_engine_timestamps.csv"
ITERATIONS = 30 #30  # Number of test iterations

baseline_df = pd.read_csv("baseline_average.csv", sep=";")
BASE_LINE_OVERHEAD = baseline_df.set_index("Search Engine")["Baseline Duration (ms)"].to_dict()

def check_internet():
    """Returns True if internet is available, False otherwise."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)  # Google's public DNS
        return True
    except OSError:
        return False

def wait_for_internet(polling_interval=10):
    """Pauses execution and waits until an internet connection is restored."""
    
    while not check_internet():
        log_message(f"No internet detected. Retrying in {polling_interval} seconds...")
        time.sleep(polling_interval)  # Wait before checking again
    
def keep_system_awake():
    """Simulate activity to prevent system sleep, cross-platform."""
    try:
        # Only perform action every 5 minutes
        if not hasattr(keep_system_awake, 'last_time') or \
           (time.time() - keep_system_awake.last_time) > 300:
            system = platform.system()
            
            if system == "Linux":
                # Use xdotool with proper syntax for negative coordinates
                try:
                    subprocess.call(['xdotool', 'mousemove_relative', '--', '1', '1'])
                    time.sleep(0.1)  # Small delay to ensure movement registers
                    subprocess.call(['xdotool', 'mousemove_relative', '--', '-1', '-1'])
                    log_message("Simulated mouse movement with xdotool")
                except FileNotFoundError:
                    log_message("xdotool not found; skipping mouse movement")
                except subprocess.CalledProcessError as e:
                    log_message(f"xdotool error: {e}")
            
            elif system == "Windows":
                # Use a simple PowerShell command to simulate a key press
                try:
                    subprocess.call(['powershell', '-Command', 'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait("{F15}")'])
                    log_message("Simulated key press on Windows")
                except subprocess.CalledProcessError as e:
                    log_message(f"Windows key press simulation failed: {e}")
            
            elif system == "Darwin":  # macOS
                # Use osascript to simulate a key press
                try:
                    subprocess.call(['osascript', '-e', 'tell application "System Events" to key code 144'])  # F15 key
                    log_message("Simulated key press on macOS")
                except subprocess.CalledProcessError as e:
                    log_message(f"macOS key press simulation failed: {e}")
            
            keep_system_awake.last_time = time.time()
    
    except Exception as e:
        log_message(f"Error in keep_system_awake: {e}")

def log_message(message):
    """Print a timestamped log message."""
    print(f"[{datetime.now()}] {message}")

def warm_up(duration=DEFAULT_WARMUP):
    log_message(f"Warming up system for {duration} seconds...")
    def fib(n):
        if n <= 1:
            return n
        return fib(n - 1) + fib(n - 2)
    
    start_time = time.time()
    while time.time() - start_time < duration:
        fib(30)
    log_message("Warm-up complete.")

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

def handle_google(driver, query):
    try:
        # Avoid maximizing window unless necessary (most modern sites don’t need it)
        # driver.maximize_window()

        # 1. Handle consent dialog efficiently
        consent_button_xpath = "//*[text()[normalize-space()='Accept All'] or text()[normalize_space()='Alles accepteren']]"
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

        # 2. Perform the search
        search_box = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.NAME, "q"))
        )
        
        # Send query all at once instead of character-by-character
        search_box.clear()
        search_box.send_keys(query)
        
        # Submit immediately with Enter key (no random delay)
        search_box.send_keys(Keys.RETURN)
        
        # Minimal wait for results (adjust based on your needs)
        time.sleep(1)
        return True
        
    except Exception as e:
        log_message(f"Error with Google search: {e}")
        return False
    
def handle_yahoo(driver, query):
    """
    Enhanced Yahoo search handler that tries only once.
    """
    try:

        # Clear cookies and cache if needed (this block can be retained if it’s useful for a single attempt)
        driver.delete_all_cookies()
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        time.sleep(random.uniform(1, 2))

        # Set timeouts, viewport, and disable webdriver flags
        driver.set_page_load_timeout(20)
        driver.set_script_timeout(15)
        width = random.randint(1024, 1920)
        height = random.randint(768, 1080)
        driver.set_window_size(width, height)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            """
        })

        # Wait for page load and simulate human actions (scroll, cookie consent, etc.)
        try:
            WebDriverWait(driver, random.uniform(5, 8)).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            pass
        driver.execute_script(f"window.scrollTo(0, {random.randint(50, 200)});")
        time.sleep(random.uniform(0.5, 1.5))

        # Handle cookie consent
        try:
            consent_buttons = driver.execute_script("""
                return Array.from(document.querySelectorAll('button')).filter(btn => 
                    ['Accept All', 'Alles accepteren'].some(text => 
                        btn.textContent.toLowerCase().includes(text.toLowerCase())
                    )
                );
            """)
            if consent_buttons:
                button = random.choice(consent_buttons)
                driver.execute_script("arguments[0].click();", button)
                time.sleep(random.uniform(1, 2))
        except Exception:
            pass

        # Find and use the search box
        selectors = [
            "document.querySelector('#ybar-sbq')",
            "document.querySelector('input[name=\"p\"]')",
            "document.querySelector('input[type=\"search\"]')",
            "document.querySelector('form#ybar-search-form input')",
            "document.querySelector('#header-search-input')"
        ]
        random.shuffle(selectors)
        search_box = None
        for selector in selectors:
            search_box = driver.execute_script(f"return {selector}")
            if search_box:
                break

        if not search_box:
            raise Exception("Search box not found")

        search_box.clear()
        time.sleep(random.uniform(0.5, 1.5))
        for char in query:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
        time.sleep(random.uniform(0.5, 1.5))

        original_handle = driver.current_window_handle

        # Submit search
        submit_methods = [
            lambda: search_box.send_keys(Keys.RETURN),
            lambda: driver.execute_script("arguments[0].form.submit();", search_box),
            lambda: driver.execute_script("""
                const btn = document.querySelector('button[type="submit"]');
                if (btn) btn.click();
            """)
        ]
        random.shuffle(submit_methods)
        submitted = False
        for method in submit_methods:
            try:
                method()
                submitted = True
                break
            except Exception:
                continue

        if not submitted:
            raise Exception("Failed to submit search")

        time.sleep(random.uniform(1, 2))
        if len(driver.window_handles) > 1:
            for handle in driver.window_handles:
                if handle != original_handle:
                    driver.switch_to.window(handle)
                    break

        WebDriverWait(driver, random.uniform(5, 8)).until(
            lambda d: d.execute_script(
                "return Boolean(document.querySelector('.searchCenterMiddle, #results, .algo, #web'))"
            )
        )
        print("Search successful!")
        time.sleep(random.uniform(0.5, 1.5))
        return True

    except TimeoutException:
        print("Yahoo search error: Results not found")
        return False
    except Exception as e:
        print(f"Yahoo search error: {str(e)}")
        return False

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
    
def handle_bing(driver, query):
    """Handle Bing search with improved error handling and multiple fallback methods"""
    try:
        log_message("Opening Bing...")
        time.sleep(2)  # Wait for page load
        
        # Handle cookie consent with explicit wait
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "bnp_btn_accept"))
            )
            if safe_click(driver, cookie_button):
                log_message("Accepted cookies")
                time.sleep(1)
            else:
                log_message("Failed to click cookie accept button")
        except TimeoutException:
            log_message("No cookie dialog or already accepted")
        
        # Find and interact with search box
        try:
            search_box = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "sb_form_q"))
            )
            
            # Clear existing text and enter query
            search_box.clear()
            search_box.send_keys(query)
            time.sleep(1)  # Wait after typing
            
            # Try multiple submission methods
            try:
                # Method 1: Press Enter
                search_box.send_keys(Keys.RETURN)
                log_message("Search submitted via Enter key")
            except Exception:
                try:
                    # Method 2: Click search button
                    search_button = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "search_icon"))
                    )
                    if safe_click(driver, search_button):
                        log_message("Search submitted via button click")
                    else:
                        # Method 3: Submit form via JavaScript
                        search_form = driver.find_element(By.ID, "sb_form")
                        driver.execute_script("arguments[0].submit();", search_form)
                    log_message("Search submitted via form submission")
                except Exception as e:
                    log_message(f"All search submission methods failed: {str(e)}")
                    return False
            
            # Wait for results to load
            time.sleep(2)
            return True
            
        except Exception as e:
            log_message(f"Error interacting with search box: {str(e)}")
            return False
            
    except Exception as e:
        log_message(f"Error during Bing search: {str(e)}")
        return False
    
def handle_duckduckgo(driver, query):
    try:
        # Find the search box
        search_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "searchbox_input"))
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        return True
    except TimeoutException:
        # Try alternative selector
        try:
            search_box = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            return True
        except Exception as e:
            log_message(f"Error with DuckDuckGo search: {e}")
            return False

def handle_ecosia(driver, query):
    try:
        # Handle cookie consent
        try:
            cookie_accept = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept all')]"))
            )
            cookie_accept.click()
            time.sleep(1)
        except TimeoutException:
            log_message("No cookie dialog on Ecosia or already accepted")
        
        # Find and use the search box
        search_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        return True
    except Exception as e:
        log_message(f"Error with Ecosia search: {e}")
        return False

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

def handle_default_search(driver, query):
    try:
        # Try common search box selectors
        selectors = [
            (By.NAME, "q"),
            (By.NAME, "query"),
            (By.NAME, "search"),
            (By.CSS_SELECTOR, "input[type='search']"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.XPATH, "//input[@placeholder='Search']"),
            (By.XPATH, "//input[contains(@placeholder, 'search')]"),
            (By.XPATH, "//input[contains(@placeholder, 'Search')]")
        ]
        
        search_box = None
        for selector_type, selector_value in selectors:
            try:
                search_box = WebDriverWait(driver, 1).until(
                    EC.presence_of_element_located((selector_type, selector_value))
                )
                break
            except TimeoutException:
                continue
        
        if search_box:
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            return True
        else:
            log_message("Could not find search box with common selectors")
            return False
            
    except Exception as e:
        log_message(f"Error with search: {e}")
        return False
    
class DriverManager:
    _driver = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            log_message("Initializing persistent Selenium driver...")
            cls._driver = setup_driver()
            if cls._driver is None:
                raise Exception("Failed to initialize the Selenium driver.")
            log_message("Persistent driver initialized.")
        return cls._driver

    @classmethod
    def quit_driver(cls):
        if cls._driver is not None:
            log_message("Quitting persistent driver...")
            cls._driver.quit()
            cls._driver = None
            log_message("Driver closed.")

def test_search_engine(engine, url, query, duration, baseline_overheads, driver):
    log_message(f"Testing {engine}")
   
    # Log start time
    start_time = int(datetime.now().timestamp() * 1000)  # Convert to milliseconds

    # Set up WebDriver with anti-detection measures
    driver.get(url)
   

    # Add a small random delay to appear more human-like
    time.sleep(random.uniform(0.5, 1.5))
    
    # Initialize success flag
    search_success = False
    
    # Use engine-specific handlers
    handlers = {
        "Google": handle_google,
        "Yahoo": handle_yahoo,
        "Bing": handle_bing,
        "DuckDuckGo": handle_duckduckgo,
        "Ecosia": handle_ecosia,
        "Startpage": handle_startpage
    }
    
    search_success = handlers.get(engine, handle_default_search)(driver, query)
    
    # If search was successful, wait for the specified duration
    if search_success:
        wait_time = 60
        log_message(f"Waiting {wait_time:.1f} seconds before next query...")
        time.sleep(wait_time)
        
        # Log end time
        end_time = int(datetime.now().timestamp() * 1000)
        
        wait_for_internet()

        keep_system_awake()

        # Clean up
        driver.delete_all_cookies()
        
        raw_duration = end_time - start_time
        baseline = baseline_overheads.get(engine, 0)
        normalized_duration = raw_duration - baseline if raw_duration > baseline else 0
        
        return {
            "Search Engine": engine,
            "Start Time": start_time,
            "End Time": end_time,
            "Raw Duration (ms)": raw_duration,
            "Baseline Overhead (ms)": baseline,
            "Normalized Duration (ms)": normalized_duration
        }
    else:
        log_message(f"Search failed for {engine}")
        driver.delete_all_cookies()
        return None

def run_tests(engines, queries, duration, baseline_overheads, driver):
    results = []

    # Shuffle both engines and queries
    shuffled_engines = list(engines.items())
    random.shuffle(shuffled_engines)
    random.shuffle(queries)

    for query in queries:  # Loop over all search queries
        log_message(f"Testing query: {query}")
        for engine, url in shuffled_engines:
            # Test the search engine
            result = test_search_engine(engine, url, query, duration, baseline_overheads, driver)
            if result:
                results.append(result)
                log_message(f"Successfully tested {engine}")
            else:
                log_message(f"Failed to test {engine}")
            
    log_message(f"Waiting {duration:.1f} seconds before next test...")
    time.sleep(duration)
    
    return results

def save_results(results, output_file):
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save as CSV
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    log_message(f"Results saved to {output_file}")
    
    # Print summary
    tested_engines = set(result['Search Engine'] for result in results)
    log_message(f"Successfully tested {len(tested_engines)} out of {len(SEARCH_ENGINES)} search engines")

    log_message(f"Engines tested: {', '.join(tested_engines)}")
    
    missing_engines = set(SEARCH_ENGINES.keys()) - set(result['Search Engine'] for result in results)
    if missing_engines:
        log_message(f"Engines that failed: {', '.join(missing_engines)}")

def main():
    log_message("Starting search engine energy measurement")
    log_message("Make sure your system is in zen mode (minimal background processes)")
    all_results = []

    # Perform system warm-up
    warm_up()
    
    log_message(f"Baseline overheads: {BASE_LINE_OVERHEAD}")
    driver = DriverManager.get_driver()

    for i in range(ITERATIONS):
        log_message(f"--- Iteration {i + 1} of {ITERATIONS} ---")
        # Run tests on all search engines for all queries in this iteration
        results = run_tests(
            engines=SEARCH_ENGINES,
            queries=SEARCH_QUERIES,
            duration=DEFAULT_DURATION,
            baseline_overheads=BASE_LINE_OVERHEAD,
            driver=driver
        )
        
        # Append an iteration number to each result for later grouping
        if results:
            for r in results:
                r["Iteration"] = i + 1
            all_results.extend(results)
        else:
            log_message("No results returned in this iteration.")
        
    
    # Save all results from all iterations to the same CSV file.
    save_results(all_results, OUTPUT_FILE)
    log_message("Measurement complete!")
    DriverManager.quit_driver()

if __name__ == "__main__":
    main()