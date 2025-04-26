import requests
import pandas as pd
import json
from datetime import datetime
import matplotlib.pyplot as plt
import os
import collections
import time

# Keepa API configuration
API_KEY = "bdmmpr7jl1pq9iopubktrp53a9r31m4otho1btpd5fv10n30lf8hje1c3ah3vdng"
ASIN = "B08HR6ZBYJ"
DOMAIN = 1  # 1 for Amazon.com
OUTPUT_DIR = "output"  # Default output directory

# RTX 3090 release date (September 1, 2020)
PRODUCT_RELEASE_DATE = datetime(2020, 9, 1)

# Minimum valid price for the product (to filter out shipping-only updates)
# RTX 3090 would never be less than $500
MIN_VALID_PRICE = 500.0

# Keepa price type indices
# Based on documentation: https://keepa.com/#!discuss/t/price-history-indices-explanation-of-csv-field/116
AMAZON = 0        # Amazon price
NEW = 1           # Marketplace/3rd party New price
USED = 2          # Marketplace/3rd party Used price
SALES = 3         # Sales Rank
LISTING = 4       # Listed since (?) not entirely clear
NEW_FBA = 5       # Amazon price for new products through FBA
RATING = 6        # Rating (out of 5)
NEW_FBM_SHIPPING = 7  # New, Fulfilled by Merchant price + shipping
LIGHTNING_DEAL = 8
WAREHOUSE = 9
NEW_PRIME = 10
COUNT_NEW = 11
COUNT_USED = 12
COUNT_REFURBISHED = 13
NEW_BUY_BOX_SHIPPING = 14
USED_BUY_BOX_SHIPPING = 15
USED_FBA_SHIPPING = 16
COUNT_REVIEWS = 17
BUY_BOX_PRICE = 18    # Buy Box price
BUY_BOX_SHIPPING = 19 # Buy Box shipping
NEW_OFFER_COUNT = 20
NEW_AMAZON_SHIPPING = 21
USED_AMAZON_SHIPPING = 22
TRADE_IN = 23

# Price types that contain actual product prices (not just shipping)
PRODUCT_PRICE_TYPES = {
    AMAZON: "Amazon",
    NEW: "New 3rd Party",
    USED: "Used 3rd Party",
    NEW_FBA: "New FBA",
    NEW_FBM_SHIPPING: "New FBM Shipping",
    WAREHOUSE: "Warehouse Deals",
    NEW_PRIME: "Prime Exclusive",
    NEW_BUY_BOX_SHIPPING: "New Buy Box Shipping",
    BUY_BOX_PRICE: "Buy Box Price"
}

# Price types that contain shipping costs
SHIPPING_PRICE_TYPES = {
    BUY_BOX_SHIPPING: "Buy Box Shipping",
    USED_BUY_BOX_SHIPPING: "Used Buy Box Shipping",
    NEW_AMAZON_SHIPPING: "New Amazon Shipping",
    USED_AMAZON_SHIPPING: "Used Amazon Shipping"
}

def get_product_data(asin=ASIN, domain=DOMAIN, api_key=API_KEY, update=1, buybox=1):
    """
    Fetch product data from Keepa API
    
    Args:
        asin: Amazon ASIN
        domain: Amazon domain (1=US, 2=UK, etc.)
        api_key: Keepa API key
        update: Whether to force data refresh (0=no, 1=yes)
        buybox: Whether to include Buy Box data (0=no, 1=yes)
    """
    # Force an update to get the latest data
    url = f"https://api.keepa.com/product?key={api_key}&domain={domain}&asin={asin}&stats=180&update={update}&buybox={buybox}"
    print(f"Requesting data with forced update from Keepa API for ASIN {asin}...")
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    
    # Save raw response for debugging
    data = response.json()
    
    # Save the raw JSON for debugging
    debug_dir = os.path.join(OUTPUT_DIR, 'debug')
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)
    
    with open(os.path.join(debug_dir, f"{asin}_raw_response.json"), 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

def keepa_time_to_datetime(keepa_time):
    """Convert Keepa time to datetime"""
    if keepa_time is None or keepa_time == -1:
        return None
    unix_time_ms = (keepa_time + 21564000) * 60000
    return datetime.fromtimestamp(unix_time_ms / 1000)

def is_valid_date(date, release_date=PRODUCT_RELEASE_DATE):
    """Check if date is valid (not before product release)"""
    if date is None:
        return False
    
    # Filter out dates before product release
    if date < release_date:
        return False
    
    # Filter out dates too far in the future (more than 2 years from now)
    # This allows for near-future dates that Keepa might have in their data
    two_years_future = datetime.now().replace(year=datetime.now().year + 2)
    if date > two_years_future:
        return False
    
    return True

def is_valid_price(price, min_price=MIN_VALID_PRICE):
    """Check if price is valid (not just shipping cost)"""
    return price >= min_price

def process_buybox_data(data):
    """
    Process ONLY Buy Box price data from Keepa API response
    """
    if not data or 'products' not in data or not data['products']:
        print("No product data found")
        return None
    
    product = data['products'][0]
    print(f"\nProduct ASIN: {product.get('asin')}")
    
    # Get product release date if available
    if 'releaseDate' in product and product['releaseDate'] > 0:
        release_date = keepa_time_to_datetime(product['releaseDate'])
        if release_date:
            print(f"Product release date: {release_date.strftime('%Y-%m-%d')}")
            global PRODUCT_RELEASE_DATE
            PRODUCT_RELEASE_DATE = release_date
    
    # Get tracking since date
    if 'trackingSince' in product and product['trackingSince'] > 0:
        tracking_since = keepa_time_to_datetime(product['trackingSince'])
        if tracking_since:
            print(f"Keepa tracking since: {tracking_since.strftime('%Y-%m-%d')}")
    
    # Get last update date
    if 'lastUpdate' in product and product['lastUpdate'] > 0:
        last_update = keepa_time_to_datetime(product['lastUpdate'])
        if last_update:
            print(f"Last data update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get the CSV data which contains price history
    csv_data = product.get('csv', [])
    
    # Create price history dictionary (datetime string -> price)
    price_history = {}
    
    # Process Buy Box price data
    if BUY_BOX_PRICE < len(csv_data) and csv_data[BUY_BOX_PRICE]:
        buybox_data = csv_data[BUY_BOX_PRICE]
        print(f"Found Buy Box price data, length: {len(buybox_data)}")
        
        # Track statistics
        invalid_dates = 0
        oldest_date = None
        newest_date = None
        
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
                        
                        # Keepa stores prices in cents, divide by 100 to get actual price
                        actual_price = price / 100 if price > 0 else None
                        
                        if actual_price and is_valid_date(date):
                            # Use ISO format for datetime string
                            date_str = date.isoformat()
                            price_history[date_str] = actual_price
                            
                            # Track date range
                            if oldest_date is None or date < oldest_date:
                                oldest_date = date
                            if newest_date is None or date > newest_date:
                                newest_date = date
                        else:
                            invalid_dates += 1
        
        # Report statistics
        print(f"Filtered out {invalid_dates} invalid dates")
        if oldest_date and newest_date:
            print(f"Date range: {oldest_date.strftime('%Y-%m-%d')} to {newest_date.strftime('%Y-%m-%d')}")
    
    valid_data_points = len(price_history)
    print(f"\nTotal valid Buy Box price points found: {valid_data_points}")
    
    # Get the current Buy Box price from stats if available
    if 'stats' in product:
        stats = product['stats']
        if 'current' in stats:
            current = stats['current']
            if BUY_BOX_PRICE < len(current) and current[BUY_BOX_PRICE] is not None and current[BUY_BOX_PRICE] > 0:
                current_price = current[BUY_BOX_PRICE] / 100
                print(f"Current Buy Box price from stats: ${current_price:.2f}")
                
                # Add current price to history if not already there
                now_str = datetime.now().isoformat()
                price_history[now_str] = current_price
    
    if valid_data_points > 0:
        # Sort the dictionary by date
        sorted_price_history = collections.OrderedDict(sorted(price_history.items()))
        return sorted_price_history
    
    return price_history

def extract_buybox_stats(data):
    """Extract Buy Box specific statistics from the Keepa API response"""
    if not data or 'products' not in data or not data['products']:
        return None
    
    product = data['products'][0]
    
    if 'stats' not in product:
        return None
    
    stats = product['stats']
    buybox_stats = {}
    
    # Add last update timestamp
    if 'lastUpdate' in product:
        last_update = keepa_time_to_datetime(product['lastUpdate'])
        if last_update:
            buybox_stats['lastUpdate'] = last_update.isoformat()
    
    # Current Buy Box info
    if 'current' in stats:
        current = stats['current']
        if BUY_BOX_PRICE < len(current) and current[BUY_BOX_PRICE] is not None and current[BUY_BOX_PRICE] > 0:
            buybox_stats['current_price'] = current[BUY_BOX_PRICE] / 100
    
    # Buy Box specific fields from stats
    buybox_fields = [
        'buyBoxPrice', 'buyBoxShipping', 'buyBoxIsUnqualified', 'buyBoxIsShippable',
        'buyBoxIsPreorder', 'buyBoxIsFBA', 'buyBoxIsAmazon', 'buyBoxIsMAP',
        'buyBoxIsUsed', 'buyBoxIsBackorder', 'buyBoxIsPrimeExclusive',
        'buyBoxIsFreeShippingEligible', 'buyBoxIsPrimePantry', 'buyBoxIsPrimeEligible',
        'buyBoxCondition', 'buyBoxAvailabilityMessage', 'buyBoxSellerId', 'lastBuyBoxUpdate'
    ]
    
    for field in buybox_fields:
        if field in stats:
            if field in ['buyBoxPrice', 'buyBoxShipping'] and stats[field] is not None:
                # Convert cents to dollars
                buybox_stats[field] = stats[field] / 100
            elif field == 'lastBuyBoxUpdate' and stats[field] is not None:
                # Convert to datetime
                last_bb_update = keepa_time_to_datetime(stats[field])
                if last_bb_update:
                    buybox_stats[field] = last_bb_update.isoformat()
            else:
                buybox_stats[field] = stats[field]
    
    return buybox_stats

def create_output_directory(directory=OUTPUT_DIR):
    """Create output directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def main():
    # Create output directory
    output_dir = create_output_directory()
    
    # Get product data with forced update to ensure fresh data
    data = get_product_data(update=1)
    
    if data:
        # Extract product title
        product_title = data['products'][0].get('title', 'Unknown Product')
        print(f"Product: {product_title}")
        
        # Extract Buy Box stats
        buybox_stats = extract_buybox_stats(data)
        if buybox_stats:
            print("\nBuy Box Details:")
            for key, value in buybox_stats.items():
                print(f"  {key}: {value}")
            
            # Save Buy Box stats to JSON
            buybox_stats_file = os.path.join(output_dir, f"{ASIN}_buybox_stats.json")
            with open(buybox_stats_file, 'w') as f:
                json.dump(buybox_stats, f, indent=2)
            print(f"Buy Box stats saved to {buybox_stats_file}")
        
        # Process Buy Box price history ONLY
        price_history = process_buybox_data(data)
        
        if price_history:
            # Save Buy Box price history as JSON
            price_history_file = os.path.join(output_dir, f"{ASIN}_price_history.json")
            with open(price_history_file, 'w') as f:
                json.dump(price_history, f, indent=2)
            print(f"Buy Box price history saved to {price_history_file}")
            
            # Also save as CSV for compatibility
            df = pd.DataFrame([
                {"date": datetime.fromisoformat(date_str), "price": price}
                for date_str, price in price_history.items()
            ])
            
            if not df.empty:
                # Sort by date
                df = df.sort_values('date')
                
                # Save to CSV
                csv_file = os.path.join(output_dir, f"{ASIN}_price_history.csv")
                df.to_csv(csv_file, index=False)
                print(f"Buy Box price history also saved to {csv_file}")
                
                # Create a simple price chart
                plt.figure(figsize=(12, 6))
                plt.plot(df['date'], df['price'])
                plt.title(f"Buy Box Price History for {product_title}")
                plt.xlabel('Date')
                plt.ylabel('Price ($)')
                plt.grid(True)
                plt.tight_layout()
                
                # Save the chart
                chart_file = os.path.join(output_dir, f"{ASIN}_price_chart.png")
                plt.savefig(chart_file)
                print(f"Buy Box price chart saved to {chart_file}")
        else:
            print("No Buy Box price history found for this product")
            
            if 'stats' in data['products'][0]:
                stats = data['products'][0]['stats']
                if 'current' in stats:
                    print("\nCurrent prices from stats:")
                    current = stats['current']
                    if BUY_BOX_PRICE < len(current) and current[BUY_BOX_PRICE] is not None and current[BUY_BOX_PRICE] > 0:
                        print(f"Buy Box Price: ${current[BUY_BOX_PRICE]/100:.2f}")

if __name__ == "__main__":
    main() 