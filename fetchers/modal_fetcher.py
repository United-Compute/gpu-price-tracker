import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import re
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

GPU_MAPPING = {
    # DB Name -> Modal Name
    "NVIDIA B200 SXM 192 GB": "Nvidia B200",
    "NVIDIA H200 SXM 141 GB": "Nvidia H200",
    "NVIDIA H100 SXM5 80 GB": "Nvidia H100",
    "NVIDIA A100 80GB PCle": "Nvidia A100, 80 GB",
    "NVIDIA A100 SXM4 40 GB": "Nvidia A100, 40 GB",
    "NVIDIA L40S": "Nvidia L40S",
    "NVIDIA A10G": "Nvidia A10G",
    "NVIDIA Tesla T4": "Nvidia T4",
    "NVIDIA L4": "Nvidia L4",
}

def get_modal_gpu_prices(headless=True):
    """Get Modal pricing page HTML after clicking a specific button"""
    
    url = "https://modal.com/pricing"
    # Using a more robust selector to find the button containing "Per hour".
    # Absolute XPaths are brittle and can break with minor page layout changes.
    xpath = "//button[contains(., 'Per hour')]"
    
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
    
    driver = None
    try:
        print("Starting browser to fetch Modal prices...")
        driver = webdriver.Chrome(options=chrome_options)
        
        driver.get(url)
        
        print("Waiting for page to load and 'Per hour' button to be clickable...")
        # Increased wait time for reliability on slower connections or complex pages
        wait = WebDriverWait(driver, 20)
        button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        
        print("Clicking 'Per hour' button...")
        button.click()
        
        # A short sleep to allow content to load after the click.
        time.sleep(3)
        
        html = driver.page_source
        
        print("✓ HTML fetched from Modal.")
        
        return html
        
    except Exception as e:
        print(f"An error occurred during web scraping: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def extract_gpu_prices_from_html(html_content):
    """Extract GPU prices from Modal pricing HTML based on the saved file."""
    soup = BeautifulSoup(html_content, 'html.parser')
    gpu_prices = {}
    
    try:
        # The items are in a list of divs with class 'line-item'.
        line_items = soup.find_all('div', class_='line-item')
        
        for item in line_items:
            # The GPU name is in a <p> tag with a specific class.
            name_element = item.find('p', class_='text-light-green/60')
            # The price is in a <p> tag with class 'price'.
            price_element = item.find('p', class_='price')
            
            if name_element and price_element:
                gpu_name = name_element.get_text(strip=True)
                
                # This ensures we skip non-GPU entries like CPU and Memory.
                if "Nvidia" not in gpu_name and "AMD" not in gpu_name:
                    continue
                
                price_text = price_element.get_text(strip=True)
                
                # The price is already per hour, e.g., "$3.95 / h".
                price_match = re.search(r'\$(\d+\.?\d*)', price_text)
                if price_match:
                    price_per_hour = float(price_match.group(1))
                    gpu_prices[gpu_name] = round(price_per_hour, 4)
        
        return gpu_prices
        
    except Exception as e:
        print(f"Error extracting prices from HTML: {e}")
        return {}

def get_raw_modal_prices():
    """Main function to get Modal GPU prices"""
    html_content = get_modal_gpu_prices()
    
    if not html_content:
        print("Failed to get HTML content from web.")
        return {}

    raw_prices = extract_gpu_prices_from_html(html_content)
    
    if not raw_prices:
        print("No prices found in HTML")

    return raw_prices

def process_modal_prices(gpu_rows):
    """
    Fetches Modal prices and prepares a batch update for Supabase.
    """
    raw_scraped_prices = get_raw_modal_prices()

    if not raw_scraped_prices:
        print("Could not retrieve Modal prices. Aborting update.")
        return
        
    print("Scraped Modal prices:", raw_scraped_prices)

    updates = []
    now = datetime.now().isoformat()

    # Create a reverse mapping from Modal Name -> DB Name for logging unmapped GPUs
    reverse_gpu_mapping = {v: k for k, v in GPU_MAPPING.items()}
    
    # Log any scraped GPUs that we don't have in our mapping
    for modal_name in raw_scraped_prices:
        if modal_name not in reverse_gpu_mapping:
            print(f"Warning: Scraped GPU '{modal_name}' not found in GPU_MAPPING values.")

    for db_row in gpu_rows:
        db_name = db_row['gpu_name']
        modal_name = GPU_MAPPING.get(db_name)
        
        if not modal_name:
            # This is not an error, just means we don't track this DB GPU on Modal
            continue
            
        price = raw_scraped_prices.get(modal_name)
        if price is None:
            print(f"Info: No price found on Modal for '{modal_name}' (from DB GPU '{db_name}'). It might be out of stock or unlisted.")
            continue

        modal_jsonb = db_row.get("modal") or {}
        modal_jsonb[now] = price

        updates.append({
            "id": db_row['id'],
            "modal": modal_jsonb
        })

    if updates:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase.table('gpu-price-tracker').upsert(updates).execute()
        print(f"Batch updated {len(updates)} rows with Modal prices.")
    else:
        print("No updates to perform for Modal.")