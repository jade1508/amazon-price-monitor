# scraper.py - Works on GitHub Actions (Playwright)
import pandas as pd
from playwright.sync_api import sync_playwright
import time
from datetime import datetime
import os

# Create output folder
os.makedirs("output", exist_ok=True)

# Load products
print("Loading my_products.csv...")
df = pd.read_csv("data/my_products.csv")

results = []

with sync_playwright() as p:
    # Launch headless Chromium (auto-downloaded)
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # Optional: Fake user-agent
    page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (compatible; GitHub-Actions)"})

    for _, row in df.iterrows():
        asin = row['asin']
        url = f"https://www.amazon.com/dp/{asin}"
        print(f"Scraping {asin}...")

        try:
            page.goto(url, timeout=30000)
            page.wait_for_load_state('networkidle', timeout=10000)

            # Extract price
            price_text = page.locator("span.a-price-whole").first.inner_text().strip()
            frac_text = page.locator("span.a-price-fraction").first.inner_text().strip()
            amazon_price = float(price_text + frac_text)

            diff_pct = ((amazon_price - row['current_price_usd']) / row['current_price_usd']) * 100

            results.append({
                'asin': asin,
                'child_name': child_name,
                'listing': listing,
                'size_code': size_code,
                'brand': brand,
                'my_price': row['current_price_usd'],
                'amazon_price': amazon_price,
                'diff_pct': round(diff_pct, 2),
                'timestamp': datetime.now().isoformat()
            })
            print
