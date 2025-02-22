import time
import pandas as pd
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from datetime import datetime

# Search Engines (Mainstream + Sustainable + Privacy-Focused)
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
    "MetaGer": "https://metager.org",
    "You.com": "https://you.com",
    "Perplexity AI": "https://www.perplexity.ai"
}

# Search Query
SEARCH_QUERY = "climate change effects"

# Test duration 
DURATION = 10  # Short test for checking, increase later

# Wait interval between tests (2 minutes = 120 seconds)
TEST_INTERVAL = 120

# TODO: should be 5mins at leasts when doing the test. 
duration = 1
# Store Results
results = []

def warm_up(duration=duration):
    """
    Perform a CPU-intensive warm-up (using stress-ng if available) to bring the system
    to a steady operational state.
    """
    print(f"[{datetime.now()}] Warming up system for {duration} seconds...")
    try:
        subprocess.run(["stress-ng", "--cpu", "4", "--timeout", str(duration)], check=True)
    except Exception as e:
        print(f"Warning: Warm-up encountered an error: {e}")
    print(f"[{datetime.now()}] Warm-up complete.")
print("Make sure your system is in zen mode \n")
print(f"System will be warmed up for {duration} seconds \n")
warm_up()

# Loop Through Each Search Engine
for engine, url in SEARCH_ENGINES.items():
    print(f"Testing {engine}")

    # Log Start Time
    start_time = int(datetime.now().timestamp() * 1000)  # Convert to milliseconds

    # Set Browser Options
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run without UI


    # Start WebDriver
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(2)  # Wait for page load

    try:
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(SEARCH_QUERY)
        search_box.send_keys(Keys.RETURN)
    except Exception as e:
        print(f"Error interacting with {engine}: {e}")
        driver.quit()
        continue

    time.sleep(DURATION)  # Test duration

    # Log End Time
    end_time = int(datetime.now().timestamp() * 1000)

    # Store Results
    results.append({
        "Search Engine": engine,
        "Start Time": start_time,
        "End Time": end_time
    })

    driver.quit()

    # Wait before next test
    print(f"Waiting {TEST_INTERVAL} seconds before next test...")
    time.sleep(TEST_INTERVAL)

# Save Timestamps
df = pd.DataFrame(results)
df.to_csv("search_engine_results/search_engine_timestamps.csv", index=False)

print("\nExperiment completed! Timestamps saved as 'search_engine_timestamps.csv'.")