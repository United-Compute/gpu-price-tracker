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

GPU_MAPPING = {
    "NVIDIA B200 SXM 192 GB": "Nvidia B200",
    "NVIDIA H200 SXM 141 GB": "Nvidia H200",
    "NVIDIA H100 SXM5 80 GB": "Nvidia H100",
    "NVIDIA A100 80GB PCle": "Nvidia A100, 80 GB",
    "NVIDIA A100 SXM4 40 GB": "Nvidia A100, 40 GB",
    "NVIDIA L40S": "Nvidia L40S",
    "NVIDIA A10G": "Nvidia A10G",
    "NVIDIA Tesla T4": "Nvidia T4",
}

def get_modal_gpu_prices():
    """Get Modal pricing page HTML after clicking a specific button"""
    
    url = "https://modal.com/pricing"
    xpath = "/html/body/div/div[1]/div[3]/div/div[3]/div/div[1]/div/button/div[1]/div[1]"
    
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment to hide browser
    
    try:
        print("Starting browser...")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("Navigating to Modal pricing page...")
        driver.get(url)
        
        print("Waiting for page to load...")
        time.sleep(3)
        
        print("Looking for button to click...")
        try:
            wait = WebDriverWait(driver, 10)
            button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            
            print("Clicking button...")
            button.click()
            
            print("Waiting for page to update after click...")
            time.sleep(3)
            
        except Exception as click_error:
            print(f"Could not find/click button: {click_error}")
            print("Continuing to save current page content...")
        
        print("Getting HTML content...")
        html = driver.page_source
        
        with open("modal_pricing_after_click.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        print("✓ HTML saved to modal_pricing_after_click.html")
        
        driver.quit()
        return html
        
    except Exception as e:
        print(f"Error: {e}")
        if 'driver' in locals():
            driver.quit()
        return None

def extract_gpu_prices_from_html(html_content):
    """Extract GPU prices from Modal pricing HTML"""
    from bs4 import BeautifulSoup
    import re
    
    soup = BeautifulSoup(html_content, 'html.parser')
    gpu_prices = {}
    
    try:
        # The pricing data is rendered in the page as HTML elements
        # Look for the "line-item" divs that contain GPU names and prices
        line_items = soup.find_all('div', class_='line-item')
        
        for item in line_items:
            # Get the GPU name (first paragraph with text-light-green/60 class)
            name_element = item.find('p', class_='text-light-green/60')
            if not name_element:
                continue
                
            gpu_name = name_element.get_text(strip=True)
            
            # Get the price (paragraph with "price" class)
            price_element = item.find('p', class_='price')
            if not price_element:
                continue
                
            price_text = price_element.get_text(strip=True)
            
            # Extract price value from text like "$0.001736 / sec" 
            price_match = re.search(r'^\$(\d+\.?\d*)', price_text)
            if price_match:
                price_per_sec = float(price_match.group(1))
                # Convert to per hour
                price_per_hour = price_per_sec * 3600
                gpu_prices[gpu_name] = price_per_hour
                print(f"Found: {gpu_name} -> ${price_per_hour:.2f}/hour")
        
        return gpu_prices
        
    except Exception as e:
        print(f"Error extracting prices: {e}")
        return {}

def map_modal_prices_to_gpu_mapping(modal_prices):
    """Map Modal GPU names to our database GPU names"""
    mapped_prices = {}
    
    # Reverse the GPU_MAPPING to go from Modal names to our names
    reverse_mapping = {v: k for k, v in GPU_MAPPING.items()}
    
    for modal_name, price in modal_prices.items():
        if modal_name in reverse_mapping:
            our_gpu_name = reverse_mapping[modal_name]
            mapped_prices[our_gpu_name] = price
            print(f"Mapped: {modal_name} -> {our_gpu_name} -> ${price:.2f}/hour")
        else:
            print(f"No mapping found for: {modal_name}")
    
    return mapped_prices

def get_mapped_modal_prices():
    """Main function to get Modal GPU prices mapped to our GPU names"""
    html_file = "modal_pricing_after_click.html"
    
    # Check if HTML file exists, if not fetch it
    if not os.path.exists(html_file):
        print("HTML file not found, fetching from web...")
        get_modal_gpu_prices()
    
    # Read and parse HTML file
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print("Extracting GPU prices from HTML...")
        modal_prices = extract_gpu_prices_from_html(html_content)
        
        if not modal_prices:
            print("No prices found in HTML")
            return {}
        
        print(f"Found {len(modal_prices)} GPU prices")
        
        # Map to our GPU names
        mapped_prices = map_modal_prices_to_gpu_mapping(modal_prices)
        
        return mapped_prices
        
    except Exception as e:
        print(f"Error reading HTML file: {e}")
        return {}

if __name__ == "__main__":
    prices = get_mapped_modal_prices()
    print(f"\nExtracted {len(prices)} mapped GPU prices:")
    for gpu, price in prices.items():
        print(f"  {gpu}: ${price}")