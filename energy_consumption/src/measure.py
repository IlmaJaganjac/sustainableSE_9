import os
import random
import subprocess
import time
from datetime import datetime
import random
import pandas as pd

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, WebDriverException)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Search Engines
SEARCH_ENGINES = {
    # "Google": "https://www.google.com", 
    "Bing": "https://www.bing.com",
    # "Yahoo": "https://www.yahoo.com", 
    # "DuckDuckGo": "https://www.duckduckgo.com",
    # "Brave Search": "https://search.brave.com",
    # "Ecosia": "https://www.ecosia.org",
    # "OceanHero": "https://oceanhero.today",
    # "Startpage": "https://www.startpage.com",
    # "Qwant": "https://www.qwant.com",
    # "Swisscows": "https://www.swisscows.com",
    # "Mojeek": "https://www.mojeek.com",
    # "You.com": "https://you.com",
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

DEFAULT_DURATION = 1 #60 # Search test duration in seconds
DEFAULT_WARMUP = 1 #300  # Warmup duration in seconds (should be 300 for real tests)
TEST_INTERVAL = 1 #120  # Pause between tests in seconds
OUTPUT_FILE = "search_engine_results/search_engine_timestamps.csv"
ITERATIONS = 1 #30  # Number of test iterations

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

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    # options.add_experimental_option('prefs', {
    #     'intl.accept_languages': 'en,en_US'
    # })
    
    # # Try to force Google to use English
    # options.add_argument('--accept-language=en-US,en;q=0.9')
    
    # Add user agent to appear more like a regular browser
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    
    # Disable automation flags
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Create driver
    driver = webdriver.Chrome(options=options)
    
    # Execute CDP commands to prevent detection
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
        """
    })
    
    return driver


def handle_google(driver, query):
    try:
        # Maximize window to ensure elements are visible
        driver.maximize_window()
        
        # 1. Switch to the consent iframe if present
        try:
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it(
                    (By.XPATH, "//iframe[contains(@src, 'consent.google')]")
                )
            )
            log_message("Switched to Google consent iframe")
        except TimeoutException:
            log_message("No Google consent iframe found or already handled")

        # 2. Handle consent button with multi-language support
        consent_texts = {
            "English": "Accept All",
            "Dutch": "Alles accepteren"
            # Add more languages if needed, e.g.:
            # "German": "Alle akzeptieren",
            # "French": "Tout accepter"
        }
        
        consent_accepted = False
        for lang, text in consent_texts.items():
            try:
                accept_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f"//*[text()[normalize-space()='{text}']]")
                    )
                )
                # Use ActionChains for human-like click
                actions = webdriver.ActionChains(driver)
                actions.move_to_element(accept_button).pause(random.uniform(0.5, 1)).click().perform()
                log_message(f"Clicked consent button in {lang} ('{text}')")
                consent_accepted = True
                time.sleep(random.uniform(1, 2))
                break
            except TimeoutException:
                continue
        
        if not consent_accepted:
            log_message("Could not find any known consent button text")
        
        # Always switch back to main content
        driver.switch_to.default_content()

        # 3. Perform the search
        search_box = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.NAME, "q"))
        )
        
        # Clear and input query with human-like typing
        search_box.clear()
        actions = webdriver.ActionChains(driver)
        actions.move_to_element(search_box).click()
        for char in query:
            actions.send_keys(char).pause(random.uniform(0.1, 0.3))
        actions.perform()
        
        # Submit search with random delay
        time.sleep(random.uniform(0.5, 1.5))
        try:
            search_box.send_keys(Keys.RETURN)
        except:
            # Fallback to clicking search button
            search_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.NAME, "btnK"))
            )
            actions.move_to_element(search_button).pause(random.uniform(0.5, 1)).click().perform()
        
        time.sleep(random.uniform(1, 3))  # Wait for results
        return True
        
    except Exception as e:
        log_message(f"Error with Google search: {e}")
        return False
    
def handle_yahoo(driver, query):
    try:
        # Maximize window to ensure elements are visible
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        log_message("Page load complete (document.readyState)")
        
        # 1. Handle cookie consent popup
        consent_texts = {
            "Dutch": "Alles accepteren",
            "English": "Accept All"
        }
        
        consent_accepted = False
        for lang, text in consent_texts.items():
            try:
                accept_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f"//button[contains(., '{text}')]")
                    )
                )
                actions = webdriver.ActionChains(driver)
                actions.move_to_element(accept_button).pause(random.uniform(0.5, 1)).click().perform()
                log_message(f"Clicked '{text}' on Yahoo consent popup ({lang})")
                consent_accepted = True
                time.sleep(random.uniform(2, 3))  # Wait for page to settle
                break
            except TimeoutException:
                log_message(f"No '{text}' button found")
                continue
        
        if not consent_accepted:
            log_message("No known consent button found or already accepted")

        # Wait again for page stability after cookie acceptance
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        log_message("Post-cookie page load complete")

        # 2. Perform the search
        log_message("Attempting to locate search box")
        
        # Debug: Save page source and screenshot
        with open("yahoo_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        log_message("Saved page source to 'yahoo_page_source.html'")
        driver.save_screenshot("yahoo_page.png")
        log_message("Saved screenshot to 'yahoo_page.png'")

        # Try multiple selectors
        selectors = [
            (By.ID, "yschsp"),
            (By.NAME, "p"),
            (By.CSS_SELECTOR, "input.rapid-noclick-resp"),
            (By.CSS_SELECTOR, "#ybar-sbq"),
            (By.CSS_SELECTOR, "input[type='search']"),
            (By.XPATH, "//input[@placeholder='Zoeken op het web']"),
            (By.XPATH, "//form[@id='ybar-search-form']//input")
        ]
        
        search_box = None
        for selector_type, selector_value in selectors:
            try:
                log_message(f"Trying selector {selector_type}: {selector_value}")
                search_box = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((selector_type, selector_value))
                )
                log_message(f"Search box found with {selector_type}: {selector_value}")
                break
            except TimeoutException:
                log_message(f"Selector {selector_type}: {selector_value} not found")
                continue
        
        if not search_box:
            # Last resort: JavaScript injection
            log_message("Attempting JavaScript to find search box")
            search_box = driver.execute_script("""
                return document.querySelector('input[type="search"]') || 
                       document.querySelector('input[name="p"]') || 
                       document.querySelector('#ybar-sbq');
            """)
            if search_box:
                log_message("Search box found via JavaScript")
            else:
                raise Exception("No search box found after all attempts")

        # Input query using JavaScript to bypass interaction issues
        log_message(f"Setting query '{query}' via JavaScript")
        driver.execute_script("arguments[0].value = arguments[1];", search_box, query)
        time.sleep(0.5)
        
        # Submit search
        log_message("Submitting search")
        try:
            search_box.send_keys(Keys.RETURN)
            log_message("Submitted via RETURN key")
        except:
            log_message("RETURN key failed, trying button")
            search_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            )
            search_button.click()
            log_message("Submitted via button click")
        
        time.sleep(random.uniform(1, 3))
        log_message("Search executed, waiting for results")
        return True
        
    except Exception as e:
        log_message(f"Error with Yahoo search: {e}")
        driver.save_screenshot("yahoo_error.png")
        with open("yahoo_error_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        return False
    
def handle_bing(driver, query):
    try:
        # Handle cookie consent
        try:
            cookie_accept = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "bnp_btn_accept"))
            )
            cookie_accept.click()
            time.sleep(1)
        except TimeoutException:
            log_message("No cookie dialog on Bing or already accepted")
        
        # Find and use the search box
        search_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "sb_form_q"))
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        return True
    except Exception as e:
        log_message(f"Error with Bing search: {e}")
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
    
def test_search_engine(engine, url, query, duration):
    log_message(f"Testing {engine}")

    # Log start time
    start_time = int(datetime.now().timestamp() * 1000)  # Convert to milliseconds

    # Set up WebDriver with anti-detection measures
    driver = setup_driver()
    
    # Add a small random delay to appear more human-like
    time.sleep(random.uniform(0.5, 1.5))
    
    # Open the search engine
    driver.get(url)
    
    # Add a random delay for page load
    time.sleep(random.uniform(1.5, 3.0))
    
    # Initialize success flag
    search_success = False
    
    # Use engine-specific handlers
    if engine == "Google":
        search_success = handle_google(driver, query)
    elif engine == "Yahoo":
        search_success = handle_yahoo(driver, query)
    elif engine == "Bing":
        search_success = handle_bing(driver, query)
    elif engine == "DuckDuckGo":
        search_success = handle_duckduckgo(driver, query)
    elif engine == "Ecosia":
        search_success = handle_ecosia(driver, query)
    elif engine == "Startpage":
        search_success = handle_startpage(driver, query)
    else:
        search_success = handle_default_search(driver, query)
    
    # If search was successful, wait for the specified duration
    if search_success:
        time.sleep(duration)
        
        # Log end time
        end_time = int(datetime.now().timestamp() * 1000)
        
        # Clean up
        driver.quit()
        
        return {
            "Search Engine": engine,
            "Start Time": start_time,
            "End Time": end_time
        }
    else:
        log_message(f"Search failed for {engine}")
        driver.quit()
        return None



def run_tests(engines, queries, duration, interval):
    results = []

    # Shuffle both engines and queries
    shuffled_engines = list(engines.items())
    random.shuffle(shuffled_engines)
    random.shuffle(queries)

    for query in queries:  # Loop over all search queries
        log_message(f"Testing query: {query}")
    
        for engine, url in shuffled_engines:
            # Test the search engine
            result = test_search_engine(engine, url, query, duration)
            
            if result:
                results.append(result)
                log_message(f"Successfully tested {engine}")
            else:
                log_message(f"Failed to test {engine}")
            
            # Wait before the next test
            if engine != shuffled_engines[-1][0]:  # Skip wait after the last engine
                wait_time = interval + random.uniform(0.5, 1.5)  # Add random component
                log_message(f"Waiting {wait_time:.1f} seconds before next test...")
                time.sleep(wait_time)
        
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
    
 
    for i in range(ITERATIONS):
        log_message(f"--- Iteration {i + 1} of {ITERATIONS} ---")
        # Run tests on all search engines for all queries in this iteration
        results = run_tests(
            engines=SEARCH_ENGINES,
            queries=SEARCH_QUERIES,
            duration=DEFAULT_DURATION,
            interval=TEST_INTERVAL
        )
        
        # Append an iteration number to each result for later grouping
        if results:
            for r in results:
                r["Iteration"] = i + 1
            all_results.extend(results)
        else:
            log_message("No results returned in this iteration.")
        
        # Optionally, pause between iterations to let the system settle
        time.sleep(5)
    
    # Save all results from all iterations to the same CSV file.
    save_results(all_results, OUTPUT_FILE)
    log_message("Measurement complete!")

if __name__ == "__main__":
    main()