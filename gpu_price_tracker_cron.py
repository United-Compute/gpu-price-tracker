#!/usr/bin/env python3
"""
GPU Price Tracker Cron Job
--------------------------
This script fetches price history data from Keepa API for GPUs stored in a Supabase database
and updates the database with the price history information.

For use with GitHub Actions as a scheduled job.
"""

import requests
import json
import logging
import os
import time
from datetime import datetime
import collections

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Supabase client
try:
    from supabase import create_client
except ImportError:
    logger.error("Supabase client not found. Install with 'pip install supabase'")
    exit(1)

# API Configuration
KEEPA_API_KEY = "bdmmpr7jl1pq9iopubktrp53a9r31m4otho1btpd5fv10n30lf8hje1c3ah3vdng"
SUPABASE_URL = "https://jftqjabhnesfphpkoilc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpmdHFqYWJobmVzZnBocGtvaWxjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5NzI4NzIsImV4cCI6MjA2MDU0ODg3Mn0.S0ZdRIauUyMhdVJtYFNquvnlW3dV1wxERy7YrurZyag"

DOMAIN = 1  # 1 for Amazon.com
BUY_BOX_PRICE = 18  # Buy Box price index
OUTPUT_DIR = "output"

# Create output directory if it doesn't exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def keepa_time_to_datetime(keepa_time):
    """Convert Keepa time to datetime"""
    if keepa_time is None or keepa_time == -1:
        return None
    unix_time_ms = (keepa_time + 21564000) * 60000
    return datetime.fromtimestamp(unix_time_ms / 1000)

def is_valid_date(date, release_date=datetime(2020, 1, 1)):
    """Check if date is valid"""
    if date is None:
        return False
    
    # Filter out dates before 2010 (too old to be valid)
    if date.year < 2010:
        return False
    
    # Filter out dates very far in the future (more than 5 years)
    five_years_future = datetime.now().replace(year=datetime.now().year + 5)
    if date > five_years_future:
        return False
    
    return True

def get_product_data(asin, domain=DOMAIN, api_key=KEEPA_API_KEY, update=1, buybox=1):
    """Fetch product data from Keepa API"""
    url = f"https://api.keepa.com/product?key={api_key}&domain={domain}&asin={asin}&stats=180&update={update}&buybox={buybox}"
    
    try:
        logger.info(f"Requesting data from Keepa API for ASIN {asin}")
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Error for ASIN {asin}: HTTP {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for ASIN {asin}: {str(e)}")
        return None

def process_buybox_data(data, asin):
    """Process Buy Box price data from Keepa API response"""
    if not data or 'products' not in data or not data['products']:
        logger.warning(f"No product data found for ASIN {asin}")
        return None
    
    product = data['products'][0]
    product_title = product.get('title', f"Unknown Product ({asin})")
    logger.info(f"Processing data for: {product_title}")
    
    # Get product release date if available
    release_date = datetime(2010, 1, 1)  # More lenient default release date
    if 'releaseDate' in product and product['releaseDate'] > 0:
        release_date_obj = keepa_time_to_datetime(product['releaseDate'])
        if release_date_obj:
            release_date = release_date_obj
            logger.info(f"Product release date: {release_date.isoformat()}")
    
    # Extract additional product details
    product_details = {
        "asin": asin,
        "title": product_title,
        "brand": product.get('brand', ''),
        "category": product.get('categoryTree', []),
        "features": product.get('features', []),
        "description": product.get('description', ''),
        "model": product.get('model', ''),
        "ean": product.get('eanList', []),
        "upc": product.get('upcList', []),
        "dimensions": {
            "package_height": product.get('packageHeight'),
            "package_width": product.get('packageWidth'),
            "package_length": product.get('packageLength'),
            "package_weight": product.get('packageWeight'),
            "item_weight": product.get('itemWeight')
        }
    }
    
    # Get the CSV data which contains price history
    csv_data = product.get('csv', [])
    
    # Create price history dictionary
    price_history = {}
    
    # Process Buy Box price data
    if BUY_BOX_PRICE < len(csv_data) and csv_data[BUY_BOX_PRICE]:
        buybox_data = csv_data[BUY_BOX_PRICE]
        logger.info(f"Found Buy Box price data, length: {len(buybox_data)}")
        
        # Track statistics
        invalid_dates = 0
        
        if len(buybox_data) >= 2:  # Need at least one timestamp and one price
            for i in range(0, len(buybox_data), 2):
                if i + 1 < len(buybox_data):  # Make sure we have both time and price
                    time_point = buybox_data[i]
                    price = buybox_data[i + 1]
                    
                    if price != -1:  # -1 means no data
                        date = keepa_time_to_datetime(time_point)
                        
                        if date is None:
                            invalid_dates += 1
                            continue
                        
                        # Keepa stores prices in cents, divide by 100
                        actual_price = price / 100 if price > 0 else None
                        
                        if actual_price and is_valid_date(date):
                            # Convert to string for JSON
                            date_str = date.isoformat()
                            price_history[date_str] = actual_price
                        else:
                            invalid_dates += 1
        
        logger.info(f"Filtered out {invalid_dates} invalid dates")
    
    # Add current price if available
    if 'stats' in product and 'current' in product['stats']:
        current = product['stats']['current']
        if BUY_BOX_PRICE < len(current) and current[BUY_BOX_PRICE] is not None and current[BUY_BOX_PRICE] > 0:
            current_price = current[BUY_BOX_PRICE] / 100
            now_str = datetime.now().isoformat()
            price_history[now_str] = current_price
            logger.info(f"Added current Buy Box price: ${current_price:.2f}")
    
    # Sort and return
    valid_data_points = len(price_history)
    logger.info(f"Total valid Buy Box price points: {valid_data_points}")
    
    # Get additional statistics from Keepa
    stats_info = {}
    if 'stats' in product:
        stats = product['stats']
        for key, value in stats.items():
            if key not in ['current', 'avg']:  # Skip these as they're arrays
                stats_info[key] = value
        
        # Get average prices if available
        if 'avg' in stats:
            avg = stats['avg']
            if BUY_BOX_PRICE < len(avg) and avg[BUY_BOX_PRICE] is not None and avg[BUY_BOX_PRICE] > 0:
                stats_info['avgBuyBoxPrice'] = avg[BUY_BOX_PRICE] / 100
    
    if valid_data_points > 0:
        # Sort the dictionary by date
        sorted_price_history = collections.OrderedDict(sorted(price_history.items()))
        
        # Calculate price statistics
        prices = list(sorted_price_history.values())
        price_stats = {
            "min": min(prices),
            "max": max(prices),
            "avg": sum(prices) / len(prices),
            "median": prices[len(prices) // 2] if len(prices) % 2 == 1 else 
                      (prices[len(prices) // 2 - 1] + prices[len(prices) // 2]) / 2
        }
        
        # Convert to regular dict for JSONB compatibility
        return {
            "asin": asin,
            "title": product_title,
            "product_details": product_details,
            "last_updated": datetime.now().isoformat(),
            "data_points": valid_data_points,
            "prices": dict(sorted_price_history),
            "price_stats": price_stats,
            "keepa_stats": stats_info
        }
    
    return None

def update_supabase_row(supabase_client, row_id, price_history_data):
    """Update Supabase row with price history data"""
    if not price_history_data:
        logger.warning(f"No price history data for row {row_id}")
        return False
    
    try:
        # Try to update with the full price history data
        logger.info(f"Updating row {row_id} with price history data")
        
        # Pass the Python dict directly to Supabase
        update_response = supabase_client.table('gpu-price-tracker').update(
            {"price_history": price_history_data}
        ).eq('id', row_id).execute()
        
        if hasattr(update_response, 'data') and update_response.data:
            logger.info(f"Successfully updated price history for row {row_id}")
            return True
        else:
            logger.error(f"Failed to update row {row_id}: No data in response")
            return False
            
    except Exception as e:
        logger.error(f"Error updating row {row_id}: {str(e)}")
        
        # Fallback to a simpler update if the full data fails
        try:
            # Try with just the current price as a simple test
            current_price = next(iter(price_history_data.get("prices", {}).values()), None)
            if current_price:
                simple_update = {
                    "market_price": current_price,
                    "price_history": {"last_updated": datetime.now().isoformat()}
                }
                
                logger.info(f"Attempting simplified update for row {row_id}")
                update_response = supabase_client.table('gpu-price-tracker').update(
                    simple_update
                ).eq('id', row_id).execute()
                
                if hasattr(update_response, 'data') and update_response.data:
                    logger.info(f"Successfully updated market_price for row {row_id}")
                    return True
        except Exception as inner_e:
            logger.error(f"Simplified update also failed for row {row_id}: {str(inner_e)}")
        
        return False

def save_local_json(price_history_data, asin):
    """Save price history data to local JSON file"""
    filename = os.path.join(OUTPUT_DIR, f"{asin}_price_history.json")
    try:
        with open(filename, 'w') as f:
            json.dump(price_history_data, f, indent=2)
        logger.info(f"Saved price history to {filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to save to {filename}: {str(e)}")
        return False

def main():
    """Main function to process all GPUs"""
    # Initialize Supabase client
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Connected to Supabase")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {str(e)}")
        return

    # Get rows from Supabase
    try:
        response = supabase.table('gpu-price-tracker').select('*').execute()
        if not hasattr(response, 'data') or not response.data:
            logger.error("No data returned from Supabase query")
            return
        
        data = response.data
        logger.info(f"Retrieved {len(data)} rows from Supabase")
    except Exception as e:
        logger.error(f"Failed to query Supabase: {str(e)}")
        return

    # Process each row
    successful_updates = 0
    failed_updates = 0
    
    for row in data:
        row_id = row.get('id')
        asin = row.get('amazon_asin')
        
        if not asin:
            logger.warning(f"Row {row_id}: No ASIN available, skipping")
            continue
        
        logger.info(f"Processing Row {row_id}, ASIN: {asin}")
        
        # Get product data from Keepa API
        keepa_data = get_product_data(asin)
        
        if keepa_data:
            # Process buy box data
            processed_data = process_buybox_data(keepa_data, asin)
            
            if processed_data:
                # Save locally first
                save_local_json(processed_data, asin)
                
                # Update Supabase
                if update_supabase_row(supabase, row_id, processed_data):
                    successful_updates += 1
                else:
                    failed_updates += 1
            else:
                logger.warning(f"No price history found for ASIN {asin}")
                failed_updates += 1
        else:
            logger.warning(f"Failed to fetch data for ASIN {asin}")
            failed_updates += 1
        
        # Add delay to avoid rate limits
        time.sleep(1)

    logger.info(f"Processing complete! Successful updates: {successful_updates}, Failed: {failed_updates}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unhandled exception in main: {str(e)}")
        # Re-raise to ensure proper exit code for GitHub Actions
        raise 