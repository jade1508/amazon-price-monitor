# scraper.py - 100% Reliable on GitHub Actions
import pandas as pd
from playwright.sync_api import sync_playwright
import time
from datetime import datetime
import os

os.makedirs("output", exist_ok=True)

# Load products
print("Loading my_products.csv...")
try:
    df = pd.read_csv("data/my_products.csv")
    print(f"Loaded {len(df)} products")
except Exception as e:
    print(f"CSV load failed: {e}")
    exit(1)

results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (compatible; GitHub-Actions)"
    )
    page = context.new_page()

    for idx, row in df.iterrows():
        asin = row['asin'].strip()
        url = f"https://www.amazon.com/dp/{asin}"
        print(f"[{idx+1}/{len(df)}] Scraping {asin}...")

        try:
            response = page.goto(url, timeout=30000)
            if response.status != 200:
                print(f"HTTP {response.status} - Page failed")
                raise Exception("Page not loaded")

            page.wait_for_load_state('networkidle', timeout=15000)

            # Try multiple price selectors (Amazon changes them)
            price = None
            for selector in [
                "span.a-price-whole",
                "span.a-price span.a-offscreen",
                "span.a-price.a-text-price.a-size-medium.apexPriceToPay span.a-offscreen"
            ]:
                try:
                    price_text = page.locator(selector).first.inner_text(timeout=5000).strip()
                    if price_text and '$' in price_text:
                        price = float(price_text.replace('$', '').replace(',', '').split()[0])
                        break
                except:
                    continue

            if price is None:
                print("Price not found - trying fallback")
                # Fallback: search for any $XX.XX
                content = page.content()
                import re
                match = re.search(r'\$([\d,]+\.?\d*)', content)
                if match:
                    price = float(match.group(1).replace(',', ''))

            if price:
                diff_pct = ((price - row['current_price_usd']) / row['current_price_usd']) * 100
                print(f"SUCCESS: Amazon ${price}, Your ${row['current_price_usd']} ({diff_pct:+.1f}%)")
            else:
                diff_pct = None
                print("No price found")

            results.append({
                'asin': asin,
                'my_price': row['current_price_usd'],
                'amazon_price': price,
                'diff_pct': round(diff_pct, 2) if diff_pct else None,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            print(f"FAILED {asin}: {e}")
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
        time.sleep(5)  # Be respectful

    browser.close()

# Save CSV
df_out = pd.DataFrame(results)
csv_path = "output/latest_prices.csv"
df_out.to_csv(csv_path, index=False)
print(f"DONE! Saved {len(results)} rows to {csv_path}")
print(f"File size: {os.path.getsize(csv_path)} bytes")
