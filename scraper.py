# scraper.py
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime
import os

os.makedirs("output", exist_ok=True)

# Load your products
df = pd.read_csv("data/my_products.csv")

options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

results = []
for _, row in df.iterrows():
    try:
        driver.get(f"https://www.amazon.com/dp/{row['asin']}")
        time.sleep(4)
        price = float(driver.find_element(By.CSS_SELECTOR, "span.a-price-whole").text + 
                     driver.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text)
        diff = (price - row['current_price_usd']) / row['current_price_usd'] * 100
    except:
        price, diff = None, None
    results.append({
        'asin': row['asin'], 'my_price': row['current_price_usd'],
        'amazon_price': price, 'diff_pct': round(diff, 2) if diff else None,
        'timestamp': datetime.now().isoformat()
    })
    time.sleep(3)
driver.quit()

# Save
pd.DataFrame(results).to_csv("output/latest_prices.csv", index=False)
print("Scraping done. File ready for upload.")
