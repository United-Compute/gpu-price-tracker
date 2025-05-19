import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from .env file
load_dotenv()

API_KEY = os.environ.get("LAMBDALABS_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

BASE_URL = "https://cloud.lambdalabs.com/api/v1"

LAMBDALABS_GPU_MAPPING = {
    "NVIDIA H100 SXM5 80 GB": "gpu_1x_h100_sxm5",
    "NVIDIA H100 PCIe 80 GB": "gpu_1x_h100_pcie",
    "NVIDIA A100 40GB PCle": "gpu_1x_a100",
    "NVIDIA A100 SXM4 40 GB": "gpu_1x_a100_sxm4",
    "NVIDIA GH200": "gpu_1x_gh200",
    "NVIDIA A10 PCIe": "gpu_1x_a10",
    "NVIDIA Quadro RTX 6000": "gpu_1x_rtx6000",
}

def get_instance_types():
    """
    Fetches available instance types from Lambda Labs.
    """
    if not API_KEY:
        print("Error: LAMBDALABS_API_KEY environment variable not set.")
        return None
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL or SUPABASE_KEY environment variable not set.")
        return None

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    try:
        response = requests.get(f"{BASE_URL}/instance-types", headers=headers)
        response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
        return response.json().get("data")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Lambda Labs instance types: {e}")
        return None

def process_lambdalabs_prices(gpu_rows):
    """
    Fetches Lambda Labs prices for 1x GPU instances and prepares them for Supabase update.
    """
    print("Fetching Lambda Labs GPU instances and prices for Supabase update...")
    instance_types_data = get_instance_types()

    if not instance_types_data:
        print("Could not retrieve instance types from Lambda Labs. Aborting Supabase update for Lambda.")
        return

    updates = []
    now = datetime.now().isoformat()
    
    # Create a quick lookup for instance details by their API name
    lambda_instances_details = {name: details for name, details in instance_types_data.items()}

    print("\nProcessing database entries for Lambda Labs prices:")
    print("=" * 70)
    print(f"{'Database GPU Name':<30} | {'Lambda API Instance':<20} | {'Status':<15}")
    print("=" * 70)

    for db_row in gpu_rows:
        db_gpu_name = db_row['gpu_name']
        lambda_api_name = LAMBDALABS_GPU_MAPPING.get(db_gpu_name)

        if not lambda_api_name:
            # print(f"{db_gpu_name:<30} | {'N/A':<20} | {'No mapping'}") # Optional: log if no mapping
            continue

        instance_data = lambda_instances_details.get(lambda_api_name)
        if not instance_data:
            print(f"{db_gpu_name:<30} | {lambda_api_name:<20} | {'Not in API'}")
            continue
        
        # We assume the mapping targets 1x instances.
        # The old logic used mapping_info['count'], but now the mapping directly points to a 1x instance name.
        # We verify it's indeed a 1x config based on typical naming like "gpu_1x_" if necessary,
        # or trust the mapping is curated for 1x instances.
        # For Lambda, their API instance names like "gpu_1x_..." inherently specify the count.

        instance_type_details = instance_data.get('instance_type', {})
        price_cents = instance_type_details.get('price_cents_per_hour')

        if price_cents is not None:
            price_dollars = price_cents / 100.0
            
            lambdalabs_jsonb = db_row.get("lambdalabs") or {}
            lambdalabs_jsonb[now] = price_dollars
            
            updates.append({
                "id": db_row['id'],
                "lambdalabs": lambdalabs_jsonb
            })
            print(f"{db_gpu_name:<30} | {lambda_api_name:<20} | Price: ${price_dollars:.2f}")
        else:
            print(f"{db_gpu_name:<30} | {lambda_api_name:<20} | {'Price N/A'}")
            
    print("=" * 70)

    if updates:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            supabase.table('gpu-price-tracker').upsert(updates).execute()
            print(f"\nSuccessfully batch updated {len(updates)} rows in Supabase with Lambda Labs prices.")
        except Exception as e:
            print(f"Error updating Supabase: {e}")
    else:
        print("\nNo Lambda Labs price updates to perform for Supabase.")

def display_1x_lambdalabs_prices(): # Renamed old main
    """Displays 1x Lambda Labs GPU prices based on current API data and mapping."""
    print("Fetching and displaying current 1x Lambda Labs GPU prices...")
    instance_types_data = get_instance_types()

    if instance_types_data:
        print("\n--- Lambda Labs 1x GPU Prices (Per GPU, from current API call) ---")
        # Invert mapping for this display function to iterate API results
        # and find a standard name if mapped.
        api_to_standard_name_map = {v: k for k, v in LAMBDALABS_GPU_MAPPING.items()}

        for api_instance_name, details in instance_types_data.items():
            if api_instance_name.startswith("cpu_"):
                continue

            # Check if this API instance name is one of the 1x instances we care about
            standard_name = api_to_standard_name_map.get(api_instance_name)
            
            if standard_name: # Only process if it's a mapped 1x instance
                instance_type_details = details.get('instance_type', {})
                total_price_cents = instance_type_details.get('price_cents_per_hour')

                if total_price_cents is not None:
                    price_per_gpu_dollars = total_price_cents / 100.0 # Since it's 1x, total price is per-GPU price
                    description = instance_type_details.get('description', 'N/A')
                    
                    print(f"GPU: {standard_name} (API Instance: {api_instance_name}, Desc: {description})")
                    print(f"  Price: ${price_per_gpu_dollars:.2f}/hour ({total_price_cents:.0f} cents/hour)")
                else:
                    print(f"Notice: Price missing for mapped 1x instance {api_instance_name} ({standard_name}).")
        print("--------------------------------------------------------------------")
    else:
        print("Could not retrieve instance types from Lambda Labs.")


if __name__ == "__main__":
    # This is only for testing the fetcher directly
    display_1x_lambdalabs_prices()  # Just show current Lambda prices without Supabase interaction