from fetchers.buy_box_amazon import process_buy_box_data
from fetchers.runpod_fetcher import process_runpod_prices
from fetchers.gcp_fetcher import process_gcp_prices
from fetchers.lambdalabs_fetcher import process_lambdalabs_prices
from fetchers.modal_fetcher import process_modal_prices
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def fetch_all_gpus():
    print("fetching all gpus nmowwwwwwwwwwww")
    print("SUPABASE_URL", SUPABASE_URL)
    print("SUPABASE_KEY", SUPABASE_KEY)
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = supabase.table('gpu-price-tracker').select('*').execute()
    print("all gpus", response)
    if not response.data:
        raise ValueError("No GPUs found in the database.")
    return response.data

# def aggregate_all_prices(gpu):
#     price_histories = {}
#     asin = gpu.get('amazon_asin')
#     if asin:
#         price_histories['amazon'] = fetch_keepa_price_history(asin)
#     price_histories['ebay'] = fetch_ebay_price_history(gpu['gpu_name'])
#     return price_histories

if __name__ == "__main__":
    gpus = fetch_all_gpus()
    # process_buy_box_data(gpus)
    # process_runpod_prices(gpus)
    # process_gcp_prices(gpus)
    # process_lambdalabs_prices(gpus)
    process_modal_prices(gpus)
    # process_amazon_used_data(gpus)
    #in the next step i want to 
    # for gpu in gpus:
    #     all_prices = aggregate_all_prices(gpu)
    #     print(gpu['gpu_name'], all_prices)