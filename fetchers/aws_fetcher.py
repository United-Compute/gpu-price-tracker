import boto3

def get_gpu_instance_types(region_name=None):
    """
    Retrieves a list of all GPU instance types available in a specific AWS region.

    Args:
        region_name (str, optional): The AWS region to query. 
                                     If None, uses the default region configured for Boto3.

    Returns:
        list: A list of dictionaries, where each dictionary contains details
              for a GPU instance type (InstanceType, GpuName, GpuManufacturer,
              GpuCount, GpuMemoryMiB). Returns an empty list if no GPU instances
              are found or an error occurs.
    """
    try:
        if region_name:
            ec2_client = boto3.client('ec2', region_name=region_name)
        else:
            ec2_client = boto3.client('ec2') # Uses default region

        paginator = ec2_client.get_paginator('describe_instance_types')
        gpu_instances_info = []

        for page in paginator.paginate():
            for instance_type_info in page.get('InstanceTypes', []):
                gpu_info = instance_type_info.get('GpuInfo')
                if gpu_info and gpu_info.get('Gpus'):
                    # Assuming instances have homogenous GPUs, take the first one
                    gpu_details = gpu_info['Gpus'][0] 
                    instance_details = {
                        'InstanceType': instance_type_info.get('InstanceType'),
                        'GpuName': gpu_details.get('Name'),
                        'GpuManufacturer': gpu_details.get('Manufacturer'),
                        'GpuCount': gpu_details.get('Count'),
                        'GpuMemoryMiB': gpu_details.get('MemoryInfo', {}).get('SizeInMiB')
                    }
                    gpu_instances_info.append(instance_details)
        
        return gpu_instances_info

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

if __name__ == '__main__':
    # Example usage:
    
    # Get GPU instances in the default configured region
    gpu_types_default_region = get_gpu_instance_types()
    if gpu_types_default_region:
        print("GPU Instance Types (Default Region):")
        for gpu_type in gpu_types_default_region:
            print(
                f"  Type: {gpu_type['InstanceType']}, Name: {gpu_type['GpuName']}, "
                f"Manufacturer: {gpu_type['GpuManufacturer']}, Count: {gpu_type['GpuCount']}, "
                f"Memory (MiB): {gpu_type['GpuMemoryMiB']}"
            )
    else:
        print("No GPU instance types found or error in default region.")

    print("-" * 30)

    # Or, specify a region, e.g., 'us-east-1'
    specific_region = 'us-east-1' # Change to your desired region
    gpu_types_specific_region = get_gpu_instance_types(region_name=specific_region)
    if gpu_types_specific_region:
        print(f"\nGPU Instance Types ({specific_region}):")
        for gpu_type in gpu_types_specific_region:
            print(
                f"  Type: {gpu_type['InstanceType']}, Name: {gpu_type['GpuName']}, "
                f"Manufacturer: {gpu_type['GpuManufacturer']}, Count: {gpu_type['GpuCount']}, "
                f"Memory (MiB): {gpu_type['GpuMemoryMiB']}"
            )
    else:
        print(f"No GPU instance types found or error in {specific_region}.")
