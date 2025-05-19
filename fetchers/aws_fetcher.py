import boto3
import json
import concurrent.futures # Import for threading

# Mapping from region code to human-readable name for Pricing API
# This is a simplified map. For a more robust solution,
# you might parse botocore.data.endpoints or use a more comprehensive map.
REGION_MAP = {
    "us-east-1": "US East (N. Virginia)",
    "us-east-2": "US East (Ohio)",
    "us-west-1": "US West (N. California)",
    "us-west-2": "US West (Oregon)",
    "af-south-1": "Africa (Cape Town)",
    "ap-east-1": "Asia Pacific (Hong Kong)",
    "ap-south-1": "Asia Pacific (Mumbai)",
    "ap-northeast-3": "Asia Pacific (Osaka)",
    "ap-northeast-2": "Asia Pacific (Seoul)",
    "ap-southeast-1": "Asia Pacific (Singapore)",
    "ap-southeast-2": "Asia Pacific (Sydney)",
    "ap-northeast-1": "Asia Pacific (Tokyo)",
    "ca-central-1": "Canada (Central)",
    "eu-central-1": "EU (Frankfurt)",
    "eu-west-1": "EU (Ireland)",
    "eu-west-2": "EU (London)",
    "eu-south-1": "EU (Milan)",
    "eu-west-3": "EU (Paris)",
    "eu-north-1": "EU (Stockholm)",
    "me-south-1": "Middle East (Bahrain)",
    "me-central-1": "Middle East (UAE)",
    "sa-east-1": "South America (Sao Paulo)",
    "il-central-1": "Israel (Tel Aviv)",
    "ap-southeast-3": "Asia Pacific (Jakarta)",
    "ap-southeast-4": "Asia Pacific (Melbourne)",
    "ap-south-2": "Asia Pacific (Hyderabad)",
    "eu-central-2": "EU (Zurich)",
    "eu-south-2": "EU (Spain)",
    "ca-west-1": "Canada West (Calgary)",
    # Add other regions as they become available or are needed
}

def get_region_long_name(region_code):
    return REGION_MAP.get(region_code, region_code) # Fallback to code if not in map

def get_instance_on_demand_price(region_code, instance_type, operating_system='Linux'):
    """
    Retrieves the On-Demand price for a given EC2 instance type in a specific region.
    """
    pricing_client = boto3.client('pricing', region_name='us-east-1') # Pricing API endpoint
    location = get_region_long_name(region_code)

    filters = [
        {'Type': 'TERM_MATCH', 'Field': 'ServiceCode', 'Value': 'AmazonEC2'},
        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
        {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
        {'Type': 'TERM_MATCH', 'Field': 'termType', 'Value': 'OnDemand'},
        {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'}, # Most common
        {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': operating_system},
        {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'}, # No additional software
        {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}, # For OnDemand
        # {'Type': 'TERM_MATCH', 'Field': 'licenseModel', 'Value': 'No License required'}, # Usually for Linux
    ]
    # For Linux, licenseModel is typically "No License required".
    # For Windows, it would be "Bring your own license" or a specific Windows license.
    if operating_system == 'Linux':
        filters.append({'Type': 'TERM_MATCH', 'Field': 'licenseModel', 'Value': 'No License required'})


    try:
        response = pricing_client.get_products(ServiceCode='AmazonEC2', Filters=filters)
        
        for price_item_str in response.get('PriceList', []):
            price_item = json.loads(price_item_str)
            
            on_demand_terms = price_item.get('terms', {}).get('OnDemand')
            if not on_demand_terms:
                continue

            for term_key, term_value in on_demand_terms.items():
                for _, price_dimension in term_value.get('priceDimensions', {}).items():
                    if price_dimension.get('unit') == 'Hrs':
                        price_str = price_dimension.get('pricePerUnit', {}).get('USD')
                        if price_str:
                            try:
                                return float(price_str)
                            except ValueError:
                                # Handle cases where price_str might not be a valid float string
                                print(f"Warning: Could not convert price '{price_str}' to float for {instance_type} in {region_code}")
                                return None
        return None # Price not found
    except Exception as e:
        print(f"Error fetching price for {instance_type} in {region_code}: {e}")
        return None


def get_gpu_instance_types(region_name): # region_name is now mandatory
    """
    Retrieves a list of all GPU instance types available in the specified AWS region,
    including their inferred interconnect type, total On-Demand price, and price per GPU.
    """
    try:
        ec2_client = boto3.client('ec2', region_name=region_name)
        paginator = ec2_client.get_paginator('describe_instance_types')
        gpu_instances_info = []

        for page in paginator.paginate(): 
            for instance_type_info in page.get('InstanceTypes', []):
                gpu_info = instance_type_info.get('GpuInfo')
                if gpu_info and gpu_info.get('Gpus'):
                    gpu_details = gpu_info['Gpus'][0]
                    instance_type_name = instance_type_info.get('InstanceType')
                    
                    inferred_interconnect = "PCIe (assumed)"
                    if instance_type_name:
                        if instance_type_name.startswith(("p4d", "p5", "p3dn", "trn1", "dl1", "dl2q")): 
                            inferred_interconnect = "High-Bandwidth (inferred)" 
                    
                    pricing_region = region_name 
                    on_demand_instance_price = get_instance_on_demand_price(pricing_region, instance_type_name)
                    
                    gpu_count = gpu_details.get('Count')
                    price_per_gpu_usd_hr = "N/A" 

                    if isinstance(on_demand_instance_price, float) and isinstance(gpu_count, int) and gpu_count > 0:
                        price_per_gpu_usd_hr = round(on_demand_instance_price / gpu_count, 5)
                    elif on_demand_instance_price is not None:
                        price_per_gpu_usd_hr = "N/A (count issue)"
                    
                    instance_details = {
                        'InstanceType': instance_type_name,
                        'GpuName': gpu_details.get('Name'),
                        'GpuManufacturer': gpu_details.get('Manufacturer'),
                        'GpuCount': gpu_count,
                        'GpuMemoryMiB': gpu_details.get('MemoryInfo', {}).get('SizeInMiB'),
                        'InferredInterconnect': inferred_interconnect,
                        'InstancePriceUSDhr': on_demand_instance_price if isinstance(on_demand_instance_price, float) else "N/A",
                        'PricePerGpuUSDhr': price_per_gpu_usd_hr,
                        'Region': region_name 
                    }
                    gpu_instances_info.append(instance_details)
        return gpu_instances_info
    except Exception as e:
        print(f"An error occurred in get_gpu_instance_types for region {region_name}: {e}")
        return []

if __name__ == '__main__':
    print("Starting AWS GPU Price Scan across all regions (in parallel)...")
    
    try:
        ec2_regions_client = boto3.client('ec2', region_name='us-east-1')
        aws_regions_response = ec2_regions_client.describe_regions(AllRegions=False)
        regions_to_scan = [region['RegionName'] for region in aws_regions_response.get('Regions', [])]
    except Exception as e:
        print(f"Could not fetch AWS regions: {e}. Exiting.")
        regions_to_scan = []

    if not regions_to_scan:
        print("No regions found to scan. Using a fallback list (us-east-1).")
        regions_to_scan = ['us-east-1']

    print(f"Will scan the following regions: {regions_to_scan}")

    lowest_prices_by_gpu_model = {}
    
    # Use ThreadPoolExecutor to parallelize region scanning
    # Adjust max_workers based on your needs and API limits; None usually defaults to a reasonable number.
    # For many regions, a higher number might be beneficial if not hitting API limits.
    # Let's start with a moderate number, e.g., 10, or os.cpu_count() * 2 or similar.
    # If you have many regions (e.g., 20+), a worker per region might be too much.
    # Let's try min(len(regions_to_scan), 10) or some other sensible cap.
    num_workers = min(len(regions_to_scan), 10) # Cap at 10 workers, or less if fewer regions
    if num_workers == 0 and regions_to_scan : num_workers = 1 # Ensure at least 1 worker if there are regions

    all_regional_offerings = []

    if regions_to_scan:
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Submit tasks for each region
            future_to_region = {executor.submit(get_gpu_instance_types, region_code): region_code for region_code in regions_to_scan}
            
            for future in concurrent.futures.as_completed(future_to_region):
                region_code_completed = future_to_region[future]
                try:
                    print(f"\n--- Completed Scan for Region: {region_code_completed} ---")
                    region_offerings = future.result()
                    if region_offerings:
                        all_regional_offerings.extend(region_offerings)
                    else:
                        print(f"No GPU offerings found or error in region: {region_code_completed}")
                except Exception as exc:
                    print(f"Region {region_code_completed} generated an exception: {exc}")
    
    # Process all collected offerings to find the lowest prices
    if all_regional_offerings:
        for offering in all_regional_offerings:
            gpu_name = offering.get('GpuName')
            gpu_manufacturer = offering.get('GpuManufacturer')
            gpu_memory_mib = offering.get('GpuMemoryMiB')
            price_per_gpu = offering.get('PricePerGpuUSDhr')
            current_region = offering.get('Region') # Region is already in the offering

            if gpu_name and gpu_manufacturer and gpu_memory_mib and isinstance(price_per_gpu, float):
                model_key = (gpu_name, gpu_manufacturer, gpu_memory_mib)
                
                if model_key not in lowest_prices_by_gpu_model or \
                   price_per_gpu < lowest_prices_by_gpu_model[model_key]['PricePerGpuUSDhr']:
                    lowest_prices_by_gpu_model[model_key] = offering
                    # print(f"New best price for {model_key}: {price_per_gpu} in {current_region} via {offering['InstanceType']}") # Verbose
            # else: # Useful for debugging missing data
                # print(f"Skipping offering due to missing data or invalid price: {offering}")
    else:
        print("No regional offerings were collected. Cannot determine lowest prices.")


    print("\n\n--- Lowest Price Per GPU Found Across All Scanned Regions ---")
    if lowest_prices_by_gpu_model:
        for model_key, details in sorted(lowest_prices_by_gpu_model.items()):
            print(
                f"Model: {model_key[0]} ({model_key[1]}), Memory: {model_key[2]} MiB\n"
                f"  Lowest Price/GPU: {details['PricePerGpuUSDhr']} USD/hr\n"
                f"  Instance Type: {details['InstanceType']} ({details['GpuCount']} GPU(s))\n"
                f"  Region: {details['Region']}\n"
                f"  Instance Price: {details['InstancePriceUSDhr']} USD/hr\n"
                f"  Interconnect: {details['InferredInterconnect']}\n"
            )
    else:
        print("No GPU pricing information could be compiled.")

    print("Scan complete.")

# This mapping uses GPU names from your database (keys from runpod_fetcher.GPU_MAPPING)
# as keys, and the corresponding AWS 'GpuName' (from describe-instance-types API) as values.
# If a direct AWS GpuName equivalent was not found in the provided AWS output for us-east-1,
# the value is None.

AWS_RAW_GPU_NAME_MAPPING = {
    "A10G": "A10G",
    "L40S": "L40S",
    "L4": "L4",
    "Radeon Pro V520": "Radeon Pro V520", # Manufacturer: AMD
    "T4": "T4",
    "A100": "A100",
    "T4g": "T4g",
    "V100": "V100",
    "H100": "H100",
    "H200": "H200",
    "M60": "M60", # <-- This would be added
    "Gaudi HL-205": "Gaudi HL-205"
}

# Example of how you might access it:
# db_gpu_name = "NVIDIA A100 80GB SXM"
# aws_gpu_name_for_api = AWS_GPU_MAPPING.get(db_gpu_name)
# if aws_gpu_name_for_api:
#     print(f"The AWS GpuName for '{db_gpu_name}' is '{aws_gpu_name_for_api}'")
# else:
#     print(f"No direct AWS GpuName mapping found for '{db_gpu_name}' in this list.")