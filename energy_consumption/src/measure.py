import os
import random
import subprocess
import time
from datetime import datetime
import random
import pandas as pd

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Search Engines
SEARCH_ENGINES = {
    # "Google": "https://www.google.com/?hl=en", 
    "Bing": "https://www.bing.com",
    # "Yahoo": "https://www.yahoo.com", 
    "DuckDuckGo": "https://www.duckduckgo.com",
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
    "react setstate sub property",
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
ITERATIONS = 3 #30  # Number of test iterations

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
        # Switch into the consent iframe (if present) and click the accept button.
        try:
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it(
                    (By.CSS_SELECTOR, "iframe[src^='https://consent.google.com']")
                )
            )
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@id='introAgreeButton']"))
            ).click()
            time.sleep(2)  # Allow time for the dialog to close.
            driver.switch_to.default_content()
        except Exception as e:
            log_message("No consent iframe found on Google or already handled: " + str(e))

        # Now wait for the search box to be visible and clickable.
        search_box = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.NAME, "q"))
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        
        # Wait for search results to load.
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "search"))
        )
        return True
    except Exception as e:
        log_message("Error with Google search: " + str(e))
        return False


def handle_yahoo(driver, query):
    try:
        # Accept the cookie consent (if present)
        try:
            cookie_accept = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]")
                )
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", cookie_accept)
            driver.execute_script("arguments[0].click();", cookie_accept)
            time.sleep(2)
        except Exception as e:
            log_message("No cookie dialog on Yahoo or already accepted: " + str(e))
        
        # Remove the 'target' attribute from the search form so that the query stays in the same tab.
        try:
            driver.execute_script("document.querySelector('form').removeAttribute('target');")
        except Exception as e:
            log_message("Could not remove target attribute from Yahoo search form: " + str(e))
        
        # Locate the search box using possible locators.
        search_box = None
        try:
            # Try by name ("p" is common on Yahoo).
            search_box = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.NAME, "p"))
            )
        except Exception as e:
            log_message("Could not find search box by name 'p': " + str(e))
        
        if not search_box:
            try:
                # Try by ID ("header-search-input" if available).
                search_box = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "header-search-input"))
                )
            except Exception as e:
                log_message("Could not find search box by ID 'header-search-input': " + str(e))
        
        if not search_box:
            # Fallback: generic CSS selector.
            search_box = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='text']"))
            )
        
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        
        # Wait for the search results container to load.
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "web"))
        )
        return True
    except Exception as e:
        log_message("Error with Yahoo search: " + str(e))
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
    log_message(f"Successfully tested {len(results)} out of {len(SEARCH_ENGINES)} search engines")
    log_message(f"Engines tested: {', '.join(result['Search Engine'] for result in results)}")
    
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