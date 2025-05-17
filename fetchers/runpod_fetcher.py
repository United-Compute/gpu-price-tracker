import os
import runpod
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

RUNPOD_KEY = os.getenv("RUNPOD_KEY")


GPU_MAPPING = {
    "MI300X": "MI300X",
    "NVIDIA A100 80GB PCle": "A100 PCIe",
    "NVIDIA A100 80GB SXM": "A100 SXM",
    "NVIDIA A30 PCIe": "A30",
    "NVIDIA A40 PCIe": "A40",
    "NVIDIA B200 SXM 192 GB": "B200 SXM",
    "NVIDIA GeForce RTX 3090": "RTX 3090",
    "NVIDIA GeForce RTX 3090 Ti": "RTX 3090 Ti",
    "NVIDIA GeForce RTX 4070 Ti": "RTX 4070 Ti",
    "NVIDIA GeForce RTX 4080": "RTX 4080",
    "NVIDIA GeForce RTX 4080 SUPER": "RTX 4080 SUPER",
    "NVIDIA GeForce RTX 4090": "RTX 4090",
    "NVIDIA GeForce RTX 5080": "RTX 5080",
    "NVIDIA GeForce RTX 5090": "RTX 5090",
    "NVIDIA H100 SXM5 80 GB": "H100 SXM",
    "NVIDIA H100 PCIe 80 GB": "H100 PCIe",
    "NVIDIA H200 SXM 141 GB": "H200 SXM", 
    "NVIDIA L4": "L4",
    "NVIDIA L40": "L40",
    "NVIDIA L40S": "L40S",
    "NVIDIA L40S": "L40S",
    "NVIDIA L40S": "L40S",
    "NVIDIA RTX 2000 Ada Generation": "RTX 2000 Ada",
    "NVIDIA RTX 4000 Ada Generation": "RTX 4000 Ada",
    "NVIDIA RTX 4000 SFF Ada Generation": "RTX 4000 Ada SFF",
    "NVIDIA RTX 5000 Ada Generation": "RTX 5000 Ada",
    "NVIDIA RTX 6000 Ada Generation": "RTX 6000 Ada",
    "NVIDIA RTX A2000": "RTX A2000",
    "NVIDIA RTX A4000": "RTX A4000",
    "NVIDIA RTX A4500": "RTX A4500",
    "NVIDIA RTX A5000": "RTX A5000",
    "NVIDIA RTX A6000": "RTX A6000",
    "NVIDIA RTX A6000": "RTX A6000",
    "NVIDIA Tesla V100 SXM2 32 GB": "V100 SXM2 32GB",
}

def process_runpod_data():
    """Process RunPod data for all GPUs and save to JSON"""
    if not RUNPOD_KEY:
        raise ValueError("RUNPOD_KEY not found in environment variables")
    
    # Initialize RunPod client
    runpod.api_key = RUNPOD_KEY
    
    try:
        # Get all available GPUs from RunPod
        available_gpus = runpod.get_gpus()
        gpu_prices = {}
        
        for gpu in available_gpus:
            try:
                price_data = fetch_runpod_price_data(gpu)
                if price_data:
                    gpu_prices[gpu["id"]] = price_data
                    print(f"\nProcessed {gpu['displayName']}:")
                    print(f"Secure Price: ${price_data['secure_price']}/hr")
            except Exception as e:
                print(f"Error processing {gpu['displayName']}: {str(e)}")
                continue
        
        # Save all prices to a JSON file
        output_file = "runpod_gpu_prices.json"
        with open(output_file, "w") as f:
            json.dump(gpu_prices, f, indent=2)
        print(f"\nAll GPU prices have been saved to {output_file}")
        
    except Exception as e:
        print(f"Error in process_runpod_data: {str(e)}")

def fetch_runpod_price_data(gpu):
    """Fetch secure price data for a specific GPU from RunPod"""
    try:
        gpu_id = gpu["id"]
        gpu_info = runpod.get_gpu(gpu_id)
        
        return {
            "name": gpu["displayName"],
            "id": gpu_id,
            "secure_price": gpu_info.get("securePrice"),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error fetching RunPod price data for {gpu['displayName']}: {str(e)}")
        return None

if __name__ == "__main__":
    #alright in the next step we need to save this data in the supabase database
    #
    process_runpod_data()