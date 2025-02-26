import os
import random
import subprocess
import time
from datetime import datetime
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, WebDriverException,
    ElementClickInterceptedException)
import logging

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
    "react setstate sub property",
    "bootstrap button next to input",
    "forcelayout api",
    "golang copy built in",
    "strlen",
    "java comparator interface",
    "ubuntu search packages",
    "URI uri = new URIBuilder",
    "java throw exception example",
    "mdn transform origin",
    "segmented circle css",
    "show is not a member of org.apache.spark.sql.GroupedData",
    "babel-jest can't console log in babel jest",
    "json minify"
]

DEFAULT_DURATION = 60 #60 # Search test duration in seconds
DEFAULT_WARMUP = 300 #300  # Warmup duration in seconds (should be 300 for real tests)
# TEST_INTERVAL = 120 #120  # Pause between tests in seconds
OUTPUT_FILE = "search_engine_results/search_engine_timestamps.csv"
ITERATIONS = 30 #30  # Number of test iterations

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
    """
    Enhanced Yahoo search handler with smart retry logic and support for new tabs.
    """
    def random_sleep(min_time=0.5, max_time=1.5):
        time.sleep(random.uniform(min_time, max_time))

    def simulate_human_input(element, text):
        """Simulate human-like typing"""
        for char in text:
            element.send_keys(char)
            random_sleep(0.1, 0.3)

    max_attempts = 2
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        print(f"Attempt {attempt} of {max_attempts}")

        try:
            # Randomize user agent
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
            ]
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": random.choice(user_agents)
            })

            # Clear cookies and cache on retry
            if attempt > 1:
                driver.delete_all_cookies()
                driver.execute_script("window.localStorage.clear();")
                driver.execute_script("window.sessionStorage.clear();")
                random_sleep(1, 2)

            # Set timeouts
            driver.set_page_load_timeout(20)
            driver.set_script_timeout(15)

            # Random viewport size
            width = random.randint(1024, 1920)
            height = random.randint(768, 1080)
            driver.set_window_size(width, height)

            # Disable webdriver flags
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    window.chrome = { runtime: {} };
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                """
            })

            # Wait for page load
            try:
                WebDriverWait(driver, random.uniform(5, 8)).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except TimeoutException:
                pass

            # Random scroll
            driver.execute_script(f"window.scrollTo(0, {random.randint(50, 200)});")
            random_sleep()

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
                    random_sleep(1, 2)
            except Exception:
                pass

            # Find search box
            search_box = None
            selectors = [
                "document.querySelector('#ybar-sbq')",
                "document.querySelector('input[name=\"p\"]')",
                "document.querySelector('input[type=\"search\"]')",
                "document.querySelector('form#ybar-search-form input')",
                "document.querySelector('#header-search-input')"
            ]
            random.shuffle(selectors)
            for selector in selectors:
                search_box = driver.execute_script(f"return {selector}")
                if search_box:
                    break

            if not search_box:
                raise Exception("Search box not found")

            # Clear and input query
            search_box.clear()
            random_sleep()
            simulate_human_input(search_box, query)
            random_sleep()

            # Store current window handle before submitting the search
            original_handle = driver.current_window_handle

            # Submit search using multiple methods
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
            for submit_method in submit_methods:
                try:
                    submit_method()
                    submitted = True
                    break
                except Exception:
                    continue

            if not submitted:
                raise Exception("Failed to submit search")

            # Wait briefly to allow any new tab to open
            time.sleep(random.uniform(1, 2))
            # If a new tab was opened, switch to it
            if len(driver.window_handles) > 1:
                for handle in driver.window_handles:
                    if handle != original_handle:
                        driver.switch_to.window(handle)
                        break

            # Wait for results
            WebDriverWait(driver, random.uniform(5, 8)).until(
                lambda d: d.execute_script(
                    "return Boolean(document.querySelector('.searchCenterMiddle, #results, .algo, #web'))"
                )
            )
            print("Search successful!")
            random_sleep(0.5, 1.5)
            return True

        except TimeoutException:
            print("Yahoo search error (attempt {}): Results not found".format(attempt))
            if os.getenv('DEBUG_YAHOO'):
                driver.save_screenshot(f"yahoo_error_{attempt}.png")
            if attempt >= max_attempts:
                return False
            print("Retrying...")
            random_sleep(2, 3)
        except Exception as e:
            print(f"Yahoo search error (attempt {attempt}): {str(e)}")
            if os.getenv('DEBUG_YAHOO'):
                driver.save_screenshot(f"yahoo_error_{attempt}.png")
            if attempt >= max_attempts:
                return False
            print("Retrying...")
            random_sleep(2, 3)

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
        wait_time = random.uniform(3, 5)
        time.sleep(wait_time)
        log_message(f"Waiting {wait_time:.1f} seconds before next query...")
        
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



def run_tests(engines, queries, duration):
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
            # if engine != shuffled_engines[-1][0]:  # Skip wait after the last engine
            #     wait_time = interval + random.uniform(0.5, 1.5)  # Add random component
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
    
 
    for i in range(ITERATIONS):
        log_message(f"--- Iteration {i + 1} of {ITERATIONS} ---")
        # Run tests on all search engines for all queries in this iteration
        results = run_tests(
            engines=SEARCH_ENGINES,
            queries=SEARCH_QUERIES,
            duration=DEFAULT_DURATION            # interval=TEST_INTERVAL
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

if __name__ == "__main__":
    main()