import json
import os
from datetime import datetime

# The data point we're looking for
TARGET_DATE = "2025-04-23T06:32:00"
TARGET_PRICE = 1431.99

# Load the raw Keepa response
debug_dir = os.path.join('output', 'debug')
with open(os.path.join(debug_dir, 'B08HR6ZBYJ_raw_response.json'), 'r') as f:
    data = json.load(f)

# Keepa time conversion function
def keepa_time_to_datetime(keepa_time):
    if keepa_time is None or keepa_time == -1:
        return None
    unix_time_ms = (keepa_time + 21564000) * 60000
    return datetime.fromtimestamp(unix_time_ms / 1000)

# Price types and their meanings
PRICE_TYPES = {
    0: "Amazon",
    1: "New 3rd Party",
    2: "Used 3rd Party",
    3: "Sales Rank",
    4: "Listed since",
    5: "New FBA",
    6: "Rating",
    7: "New FBM Shipping",
    8: "Lightning Deal",
    9: "Warehouse",
    10: "New Prime",
    11: "Count New",
    12: "Count Used",
    13: "Count Refurbished",
    14: "New Buy Box Shipping",
    15: "Used Buy Box Shipping",
    16: "Used FBA Shipping",
    17: "Count Reviews",
    18: "Buy Box Price",
    19: "Buy Box Shipping",
    20: "New Offer Count",
    21: "New Amazon Shipping",
    22: "Used Amazon Shipping",
    23: "Trade In"
}

# Extract the CSV data from the product
product = data['products'][0]
csv_data = product.get('csv', [])

print(f"Looking for data point: {TARGET_DATE}, price: ${TARGET_PRICE}")
print(f"Product: {product.get('title')}")

# Check each price type
for idx, name in PRICE_TYPES.items():
    if idx < len(csv_data) and csv_data[idx]:
        price_data = csv_data[idx]
        
        for i in range(0, len(price_data), 2):
            if i + 1 < len(price_data):
                time_point = price_data[i]
                price = price_data[i + 1]
                
                if price != -1:
                    date = keepa_time_to_datetime(time_point)
                    if date:
                        date_str = date.isoformat()
                        actual_price = price / 100 if price > 0 else None
                        
                        # Check if this is our target data point
                        if date_str == TARGET_DATE and abs(actual_price - TARGET_PRICE) < 0.01:
                            print(f"\nFound matching data point in price type: {idx} ({name})")
                            print(f"Date: {date_str}")
                            print(f"Price: ${actual_price}")
                            
                            # Print surrounding data points
                            print("\nSurrounding data points:")
                            start_idx = max(0, i - 6)
                            end_idx = min(len(price_data), i + 8)
                            
                            for j in range(start_idx, end_idx, 2):
                                if j + 1 < len(price_data):
                                    t = price_data[j]
                                    p = price_data[j + 1]
                                    if p != -1:
                                        d = keepa_time_to_datetime(t)
                                        if d:
                                            d_str = d.isoformat()
                                            p_val = p / 100 if p > 0 else None
                                            arrow = "==>" if j == i else "   "
                                            print(f"{arrow} {d_str}: ${p_val}") 