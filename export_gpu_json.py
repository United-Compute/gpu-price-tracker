import os
import json
from supabase import create_client
from dotenv import load_dotenv
import re

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATA_DIR = "data"

def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', name)

def fetch_all_gpus():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = supabase.table('gpu-price-tracker').select('*').execute()
    if not response.data:
        raise ValueError("No GPUs found in the database.")
    return response.data

def save_gpu_price_history_json(gpu):
    os.makedirs(DATA_DIR, exist_ok=True)
    filename = sanitize_filename(gpu.get('gpu_name', '')) + ".json"
    output_path = os.path.join(DATA_DIR, filename)
    prices = gpu.get('amazon_buy_box') or {}
    data = {
        "gpu_name": gpu.get('gpu_name', ''),
        "prices": prices
    }
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved price history JSON to {output_path}")

def main():
    gpus = fetch_all_gpus()
    for gpu in gpus:
        save_gpu_price_history_json(gpu)

if __name__ == "__main__":
    main()