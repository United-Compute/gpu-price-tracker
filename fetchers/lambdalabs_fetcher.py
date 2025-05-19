import requests
import os

API_KEY = os.environ.get("LAMBDALABS_API_KEY") # It's good practice to use environment variables for API keys
BASE_URL = "https://cloud.lambdalabs.com/api/v1"

# Mapping from Lambda Labs instance type name to a standard GPU name and count
# The 'standard_name' should match the names you use for these GPUs in your database or other records.
# You might need to adjust these 'standard_name' values to fit your exact needs.
LAMBDALABS_GPU_MAPPING = {
    "NVIDIA H100 SXM5 80 GB": "gpu_1x_h100_sxm5",
    "NVIDIA H100 PCIe 80 GB": "gpu_1x_h100_pcie",
    "NVIDIA A100 40GB PCle": "gpu_1x_a100",
    "NVIDIA A100 80GB SXM": "Tesla A100",
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

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    try:
        response = requests.get(f"{BASE_URL}/instance-types", headers=headers)
        response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
        return response.json().get("data")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching instance types: {e}")
        return None

def main():
    print("Fetching Lambda Labs GPU instances and prices...")
    instance_types_data = get_instance_types()

    if instance_types_data:
        print("\n--- Lambda Labs 1x GPU Prices (Per GPU) ---")
        for api_instance_name, details in instance_types_data.items():
            if api_instance_name.startswith("cpu_"): # Skip CPU instances
                continue

            mapping_info = LAMBDALABS_GPU_MAPPING.get(api_instance_name)
            instance_type_details = details.get('instance_type', {})
            total_price_cents = instance_type_details.get('price_cents_per_hour')

            if mapping_info and total_price_cents is not None:
                standard_name = mapping_info['standard_name']
                gpu_count = mapping_info['count']
                
                # Only process and print if it's a 1x instance
                if gpu_count == 1:
                    price_per_gpu_cents = total_price_cents / gpu_count # Will be same as total_price_cents
                    price_per_gpu_dollars = price_per_gpu_cents / 100
                    description = instance_type_details.get('description', 'N/A')
                    
                    print(f"GPU: {standard_name} (from instance: {api_instance_name}, {description})")
                    print(f"  Price per GPU: ${price_per_gpu_dollars:.2f}/hour ({price_per_gpu_cents:.0f} cents/hour)")
                    # Optionally, list regions if needed:
                    # print(f"  Regions with capacity: {', '.join(region['name'] for region in details.get('regions_with_capacity_available', []))}")
                # else:
                    # Optionally, you could add a log here if you want to see which multi-GPU instances are being skipped
                    # print(f"Skipping multi-GPU instance: {api_instance_name} (count: {gpu_count})")

            elif total_price_cents is None and not api_instance_name.startswith("cpu_"):
                 print(f"Notice: Price missing for instance type {api_instance_name}. Description: {instance_type_details.get('description', 'N/A')}")
            elif not api_instance_name.startswith("cpu_"):
                # This will also catch multi-GPU instances not in our mapping or those we want to ignore based on count
                # You might want to refine this message if you only want to warn about unmapped 1x instances.
                # For now, if it's not a 1x instance via the mapping, it won't print as a priced GPU.
                pass # Silently skip unmapped or non-1x instances that didn't hit the 'gpu_count == 1' block
        print("------------------------------------")
    else:
        print("Could not retrieve instance types.")

if __name__ == "__main__":
    main()