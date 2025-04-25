import json
import csv
import datetime
import os
import pprint

# Path to your JSON data file
json_file_path = 'test.json'
output_directory = 'price_history'

# Create output directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory, exist_ok=True)

# Keepa epoch starts on 2000-01-01 00:00:00 UTC
keepa_epoch_start = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)

def convert_keepa_time(keepa_minutes):
    """Convert Keepa time (minutes since 2000-01-01) to a datetime object"""
    return keepa_epoch_start + datetime.timedelta(minutes=keepa_minutes)

def convert_keepa_price(price_cents):
    """Convert Keepa price (cents/smallest unit) to dollars/euros"""
    if price_cents == -1:  # Out of stock
        return None
    return price_cents / 100.0

def process_price_history(raw_data, asin):
    """Process the price history data from the raw JSON"""
    if not raw_data or "products" not in raw_data or not raw_data["products"]:
        print("Error: No product data found in the JSON")
        return {}
    
    product = raw_data["products"][0]
    
    if "csv" not in product:
        print("Error: No price history data found in the product")
        return {}
    
    # Access the csv data
    csv_data = product["csv"]
    
    # Debug: Print the structure of csv_data
    print("CSV data structure:")
    data_type = type(csv_data)
    print(f"Type: {data_type}")
    
    if isinstance(csv_data, list):
        print(f"List length: {len(csv_data)}")
        if len(csv_data) > 0:
            print(f"First element type: {type(csv_data[0])}")
            if isinstance(csv_data[0], list):
                print(f"First element length: {len(csv_data[0])}")
    
    # If csv is a list, extract the price history from the nested lists
    # based on the structure revealed in test.json
    if isinstance(csv_data, list):
        print("Processing list-formatted CSV data")
        
        # The data appears to be in the first element
        if len(csv_data) > 0 and isinstance(csv_data[0], list):
            return process_list_price_data(csv_data)
        
    elif isinstance(csv_data, dict):
        return process_dict_price_data(csv_data)
    else:
        print(f"Error: Unexpected csv data format: {type(csv_data)}")
        return {}

def process_list_price_data(csv_data):
    """Process price history from list-formatted CSV data"""
    result = {}
    
    # Process each element in the csv_data list
    for idx, price_data in enumerate(csv_data):
        if not isinstance(price_data, list):
            continue
            
        # Skip empty lists
        if not price_data:
            continue
            
        price_type = f"DATA_{idx}"
        print(f"Processing {price_type} with {len(price_data)} data points")
        
        processed_data = []
        # Look for alternating timestamp/price pairs
        timestamps_and_prices = []
        
        # Check if data is already paired or needs pairing
        if len(price_data) >= 2 and all(isinstance(x, (int, float)) for x in price_data[:10]):
            # Data needs pairing (format: [ts1, price1, ts2, price2, ...])
            for i in range(0, len(price_data), 2):
                if i + 1 < len(price_data):
                    timestamps_and_prices.append((price_data[i], price_data[i+1]))
        elif len(price_data) > 0 and isinstance(price_data[0], list) and len(price_data[0]) == 2:
            # Data is already paired (format: [[ts1, price1], [ts2, price2], ...])
            timestamps_and_prices = price_data
            
        # Process the timestamp/price pairs
        for timestamp, price in timestamps_and_prices:
            # Skip entries without valid data
            if timestamp is None or price is None:
                continue
                
            # Convert timestamp to datetime
            date = convert_keepa_time(timestamp)
            
            # Skip out of stock entries (typical value is -1)
            if price == -1:
                continue
                
            # Convert price from cents to dollars/euros
            value = convert_keepa_price(price)
            
            processed_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': value
            })
        
        if processed_data:
            result[price_type] = processed_data
            print(f"  Processed {len(processed_data)} valid price points")
    
    return result

def process_dict_price_data(csv_data):
    """Process price history from dictionary-formatted CSV data"""
    print("Processing dictionary-formatted CSV data")
    available_price_types = list(csv_data.keys())
    print(f"Available price types: {available_price_types}")
    
    # Process each available price type
    result = {}
    for price_type in available_price_types:
        print(f"Processing {price_type} price history...")
        
        # Get the raw history data (alternating timestamp and price)
        history_data = csv_data[price_type]
        
        # Skip empty data
        if not history_data:
            print(f"No data available for {price_type}")
            continue
        
        # Process the data into pairs
        processed_data = []
        for i in range(0, len(history_data), 2):
            if i + 1 < len(history_data):
                timestamp = history_data[i]
                price = history_data[i+1]
                
                # Convert timestamp to datetime
                date = convert_keepa_time(timestamp)
                
                # Convert price (skip out of stock if needed)
                if price_type != 'SALES' and price == -1:
                    # Skip out of stock entries for regular price types
                    continue
                
                # For sales rank, just use the raw value
                # For prices, convert from cents to dollars/euros
                if price_type == 'SALES':
                    value = price  # Sales rank is the integer value itself
                else:
                    value = convert_keepa_price(price)
                    
                processed_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': value
                })
        
        result[price_type] = processed_data
        print(f"  Processed {len(processed_data)} data points")
    
    return result

def save_to_csv(data, asin):
    """Save processed data to CSV files"""
    if not data:
        print("No data to save")
        return
        
    for price_type, history in data.items():
        if not history:
            continue
            
        filename = f"{output_directory}/{asin}_{price_type}_history.csv"
        
        print(f"Saving {price_type} history to {filename}...")
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['date', 'value']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for entry in history:
                writer.writerow(entry)
        
        print(f"  Saved {len(history)} rows")

def main():
    print("Loading JSON data...")
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get the ASIN from the data
    if "products" in data and len(data["products"]) > 0:
        asin = data["products"][0].get("asin", "UNKNOWN")
    else:
        asin = "UNKNOWN"
    
    print(f"Processing data for ASIN: {asin}")
    
    # Process the price history
    price_history = process_price_history(data, asin)
    
    # Save to CSV files
    save_to_csv(price_history, asin)
    
    print("Processing complete!")

if __name__ == "__main__":
    main() 