from supabase import create_client
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
KEEPA_API_KEY = os.getenv("KEEPA_API_KEY")
KEEPA_DOMAIN = 1  # 1 for Amazon.com

def process_amazon_used_data(gpu_rows):
    print("amazon used data")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    updates = []

    for gpu in gpu_rows:
        asin = gpu.get('amazon_asin')
        row_id = gpu.get('id')
        release_date_str = gpu.get('release_date')
        release_date = None
        if release_date_str:
            try:
                release_date = datetime.fromisoformat(release_date_str)
            except Exception:
                release_date = None
        used_data = None

        if asin:
            try:
                used_data = fetch_keepa_used_price_history(asin, release_date)
            except Exception as e:
                print(f"Error fetching Keepa used data for ASIN {asin}: {e}")
                used_data = None
        else:
            print(f"No ASIN for row id {row_id}, skipping Keepa request.")

        updates.append({
            "id": row_id,
            "amazon_used": used_data
        })

    # Batch update using upsert
    print("updates", updates)
    if updates:
        print("updating")
        supabase.table('gpu-price-tracker').upsert(updates).execute()
        print(f"Batch updated {len(updates)} rows.")
    else:
        print("No updates to perform.")

def keepa_time_to_datetime(keepa_time):
    if keepa_time is None or keepa_time == -1:
        return None
    unix_time_ms = (keepa_time + 21564000) * 60000
    return datetime.utcfromtimestamp(unix_time_ms / 1000)

def is_valid_date(date, release_date=None):
    if date is None:
        return False
    if release_date and date < release_date:
        return False
    five_years_future = datetime.now().replace(year=datetime.now().year + 5)
    if date > five_years_future:
        return False
    return True

def fetch_keepa_used_price_history(asin, release_date=None):
    url = f"https://api.keepa.com/product?key={KEEPA_API_KEY}&domain={KEEPA_DOMAIN}&asin={asin}&buybox=1"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"Keepa API error for ASIN {asin}: {response.status_code}")
            return None
        data = response.json()
        
        print(f"\n=== Debug for ASIN {asin} ===")
        print("Response status:", response.status_code)
        
        if not data or 'products' not in data or not data['products']:
            print(f"No product data found for ASIN {asin}")
            return None
            
        product = data['products'][0]
        
        used_history = product.get('buyBoxUsedHistory', [])
        price_history = {}
        
        if used_history:
            print(f"Used history length: {len(used_history)}")
            print(f"First few entries: {used_history[:10]}")
            
            for entry in used_history:
                time_point = entry[0]
                price = entry[1]
                date = keepa_time_to_datetime(time_point)
                
                if price != -1:
                    if date and is_valid_date(date, release_date):
                        date_str = date.isoformat() + "Z"
                        price_history[date_str] = price / 100
                        print(f"Added to history: {date_str} -> {price/100}")
        
        print(f"Final price history entries: {len(price_history)}")
        return price_history if price_history else None
        
    except Exception as e:
        print(f"Exception fetching Keepa used data for ASIN {asin}: {e}")
        return None