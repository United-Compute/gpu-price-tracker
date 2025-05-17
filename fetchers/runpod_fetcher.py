import os
import runpod
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

RUNPOD_KEY = os.getenv("RUNPOD_KEY")


GPU_MAPPING = {
    "NVIDIA GeForce RTX 3090": "NVIDIA GeForce RTX 3090",
    "NVIDIA GeForce RTX 3090 Ti": "NVIDIA GeForce RTX 3080",
    "Quadro RTX 5000": "NVIDIA GeForce RTX 3070",
    "NVIDIA A100 40GB PCle": "NVIDIA GeForce RTX 3060",
    "NVIDIA GeForce RTX 5090": "NVIDIA GeForce RTX 2050",
    "NVIDIA GeForce RTX 5080": "NVIDIA GeForce RTX 2050",
    "NVIDIA GeForce RTX 4090": "NVIDIA GeForce RTX 2050",
    "NVIDIA GeForce RTX 4070": "NVIDIA GeForce RTX 2050",
    "NVIDIA GeForce RTX 4060 Ti": "NVIDIA GeForce RTX 2050",
    "NVIDIA GeForce RTX 3070": "NVIDIA GeForce RTX 2050",
    "NVIDIA GeForce RTX 2080": "NVIDIA GeForce RTX 2050",
    "NVIDIA A40 PCIe": "NVIDIA GeForce RTX 2050",
    "NVIDIA RTX A6000": "NVIDIA GeForce RTX 2050",
    "NVIDIA RTX A5000": "NVIDIA GeForce RTX 2050",
    "NVIDIA RTX A4500": "NVIDIA GeForce RTX 2050",
    "NVIDIA RTX A4000": "NVIDIA GeForce RTX 2050",
    "NVIDIA L40": "NVIDIA GeForce RTX 2050",
    "NVIDIA H100 PCIe 80 GB": "NVIDIA GeForce RTX 2050",
    "NVIDIA RTX 2000 Ada Generation": "NVIDIA GeForce RTX 2050",
    "NVIDIA RTX 6000 Ada Generation": "NVIDIA GeForce RTX 2050",
    "NVIDIA H100 PCIe 96 GB": "NVIDIA GeForce RTX 2050",
    "NVIDIA RTX 4000 Ada Generation": "NVIDIA GeForce RTX 2050"
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