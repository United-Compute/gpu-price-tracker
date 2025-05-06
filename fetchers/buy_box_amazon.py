from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def process_buy_box_data(gpu_rows):
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    updates = []

    for gpu in gpu_rows:
        asin = gpu.get('amazon_asin')
        row_id = gpu.get('id')
        buy_box_data = None

        if asin:
            try:
                buy_box_data = fetch_keepa_price_history(asin)
            except Exception as e:
                print(f"Error fetching Keepa data for ASIN {asin}: {e}")
                buy_box_data = None
        else:
            print(f"No ASIN for row id {row_id}, skipping Keepa request.")

        updates.append({
            "id": row_id,
            "amazon_buy_box": buy_box_data
        })

    # Batch update using upsert
    if updates:
        supabase.table('gpu-price-tracker').upsert(updates).execute()
        print(f"Batch updated {len(updates)} rows.")
    else:
        print("No updates to perform.")

def fetch_keepa_price_history(asin):
    # Your logic to fetch from Keepa API
    # Return the buy box data (or None if not found)
    # Example:
    # return {"2024-06-01": 1234.56, ...}
    pass