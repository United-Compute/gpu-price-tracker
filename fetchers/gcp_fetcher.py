import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
import requests
from collections import defaultdict

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("GCP_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

BASE_URL = "https://cloudbilling.googleapis.com/v1"
COMPUTE_SERVICE = "services/6F81-5844-456A"

# Map our standard GPU names to GCP's names
GCP_GPU_MAPPING = {
    "NVIDIA H100 SXM5 80 GB": "H100 80GB",
    "NVIDIA H200 SXM 141 GB": "141GB",
    "NVIDIA A100 SXM4 40 GB": "Tesla A100",
    "NVIDIA A100 80GB SXM": "Tesla A100",
    "NVIDIA L4": "L4",
    "NVIDIA Tesla T4": "Tesla T4",
    "NVIDIA Tesla V100 SXM2 16 GB": "Tesla V100",
    "NVIDIA Tesla P4": "Tesla P4",
    "NVIDIA Tesla P100 PCIe 16 GB": "Tesla P100"
}

def print_all_available_gpus(api_key):
    """Print all available GPU types from GCP, regardless of our mapping"""
    try:
        url = f"{BASE_URL}/{COMPUTE_SERVICE}/skus"
        params = {'key': api_key}

        print(f"Fetching SKUs from URL: {url}")
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            print(f"Error response: {response.status_code}")
            print(f"Response content: {response.text}")
            return
            
        data = response.json()
        
        print(f"\nAnalyzing {len(data.get('skus', []))} SKUs for unique GPU types...")
        
        # Use sets to track unique GPU types
        gpu_types = set()
        gpu_descriptions = defaultdict(set)  # To track regions per GPU type

        for sku in data.get('skus', []):
            category = sku.get('category', {})
            if category.get('resourceGroup') != 'GPU':
                continue

            description = sku.get('description', '')
            
            # Skip if it's a commitment or reserved instance
            if any(x in description.lower() for x in ['commitment', 'reserved', 'calendar mode']):
                continue

            # Extract the basic GPU name from the description
            parts = description.split()
            if len(parts) >= 3:
                # Try to extract the GPU name
                gpu_name = ' '.join(parts[1:parts.index("GPU")])
                gpu_types.add(gpu_name)
                
                # Track which regions this GPU is available in
                if ' running in ' in description:
                    region = description.split(' running in ')[-1].split()[0]
                    gpu_descriptions[gpu_name].add(region)

        # Print the results
        print("\nAvailable GPU Types on Google Cloud:")
        print("====================================")
        for gpu_name in sorted(gpu_types):
            regions = sorted(gpu_descriptions[gpu_name])
            print(f"\nGPU: {gpu_name}")
            print(f"Available in {len(regions)} regions: {', '.join(regions)}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching GPU information: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")

def get_gpu_prices(api_key):
    """Fetch GPU prices from Google Cloud Platform"""
    try:
        url = f"{BASE_URL}/{COMPUTE_SERVICE}/skus"
        params = {'key': api_key}

        print(f"Fetching SKUs from URL: {url}")
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            print(f"Error response: {response.status_code}")
            print(f"Response content: {response.text}")
            return []
            
        data = response.json()
        
        print(f"Found {len(data.get('skus', []))} SKUs")
        
        gpu_prices = []
        for sku in data.get('skus', []):
            category = sku.get('category', {})
            if category.get('resourceGroup') != 'GPU':
                continue

            description = sku.get('description', '')
            
            # Skip if it's a commitment or reserved instance
            if any(x in description.lower() for x in ['commitment', 'reserved', 'calendar mode']):
                continue

            # Find matching GPU from our mapping
            matching_gpu = None
            for db_name, gcp_name in GCP_GPU_MAPPING.items():
                if gcp_name.lower() in description.lower():
                    # Special handling for A100 to differentiate between 40GB and 80GB variants
                    if gcp_name == "Tesla A100":
                        if "80GB" in description:
                            matching_gpu = "NVIDIA A100 80GB SXM"
                        else:
                            matching_gpu = "NVIDIA A100 SXM4 40 GB"
                    else:
                        matching_gpu = db_name
                    break
            
            if matching_gpu:
                pricing_info = sku.get('pricingInfo', [])
                if pricing_info:
                    pricing = pricing_info[0]
                    pricing_expression = pricing.get('pricingExpression', {})
                    tiered_rates = pricing_expression.get('tieredRates', [])
                    
                    if tiered_rates:
                        unit_price = tiered_rates[0].get('unitPrice', {})
                        # Convert nanos to dollars
                        price_nanos = float(unit_price.get('nanos', 0)) / 1e9
                        price_units = float(unit_price.get('units', 0))
                        price = price_units + price_nanos

                        # Skip if price is 0
                        if price == 0:
                            continue

                        # Get the region without any extra text
                        region = sku.get('serviceRegions', ['unknown'])[0]
                        if ' running in ' in description:
                            region = description.split(' running in ')[-1].split()[0]

                        gpu_info = {
                            'gpu_type': matching_gpu,
                            'description': description,
                            'price_per_hour': price,
                            'region': region,
                            'usage_type': category.get('usageType', 'unknown')
                        }
                        
                        if 'OnDemand' in gpu_info['usage_type']:
                            print(f"Found GPU info: {gpu_info}")
                            gpu_prices.append(gpu_info)

        return gpu_prices

    except requests.exceptions.RequestException as e:
        print(f"Error fetching GPU prices: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        return []

def get_lowest_prices(gpu_prices):
    """Get the lowest price for each GPU type across all regions"""
    lowest_prices = {}
    
    for gpu_info in gpu_prices:
        gpu_name = gpu_info['gpu_type']  # This is our database name
        price = gpu_info['price_per_hour']
        
        if gpu_name not in lowest_prices or price < lowest_prices[gpu_name]:
            lowest_prices[gpu_name] = price
    
    print("\nLowest prices found for each GPU type:")
    for gpu, price in lowest_prices.items():
        print(f"GPU: {gpu:<20} Price: ${price:.4f}")
    
    return lowest_prices

def process_gcp_prices(gpu_rows):
    """Process and update GPU prices in Supabase"""
    gpu_prices = get_gpu_prices(API_KEY)
    lowest_prices = get_lowest_prices(gpu_prices)
    
    updates = []
    now = datetime.now().isoformat()

    print("\nProcessing database mappings:")
    print("=" * 50)
    print(f"{'Database Name':<40} | {'GCP Name':<20} | {'Price':<10}")
    print("=" * 50)

    for db_row in gpu_rows:
        db_name = db_row['gpu_name']
        if db_name not in GCP_GPU_MAPPING:
            print(f"{db_name:<40} | {'No mapping':<20} | {'N/A':<10}")
            continue

        # Look up price directly using database name
        price = lowest_prices.get(db_name)  # Changed from gcp_name to db_name
        
        if price is None:
            print(f"{db_name:<40} | {GCP_GPU_MAPPING[db_name]:<20} | {'No price':<10}")
            continue

        print(f"{db_name:<40} | {GCP_GPU_MAPPING[db_name]:<20} | ${price:<9.4f}")

        # Fetch existing JSONB or start new
        gcp_jsonb = db_row.get("gcp") or {}
        gcp_jsonb[now] = price

        updates.append({
            "id": db_row['id'],
            "gcp": gcp_jsonb
        })

    print("\nSummary:")
    print(f"Total GPUs in database: {len(gpu_rows)}")
    print(f"Successfully mapped and found prices: {len(updates)}")
    print(f"Failed to map or find prices: {len(gpu_rows) - len(updates)}")

    # Batch update using upsert
    if updates:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase.table('gpu-price-tracker').upsert(updates).execute()
        print(f"\nBatch updated {len(updates)} rows with GCP prices.")
    else:
        print("\nNo updates to perform.")

def main():
    print("Starting GPU discovery...")
    print_all_available_gpus(API_KEY)
    
    print("\nNow fetching prices for mapped GPUs...")
    gpu_prices = get_gpu_prices(API_KEY)
    
    # Print the price results
    print("\nGoogle Cloud Platform GPU Prices:")
    print("=================================")
    if not gpu_prices:
        print("No GPU prices found")
    else:
        # Sort by GPU type and region
        gpu_prices.sort(key=lambda x: (x['gpu_type'], x['region']))
        for gpu in gpu_prices:
            print(f"\nGPU Type: {gpu['gpu_type']}")
            print(f"Region: {gpu['region']}")
            print(f"Price per hour: ${gpu['price_per_hour']:.4f}")
            print(f"Usage Type: {gpu['usage_type']}")

    # Get existing GPU rows from Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = supabase.table('gpu-price-tracker').select('*').execute()
    gpu_rows = result.data
    
    process_gcp_prices(gpu_rows)

if __name__ == "__main__":
    main()