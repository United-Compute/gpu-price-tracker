import os
import runpod
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from .env file
load_dotenv()

RUNPOD_KEY = os.getenv("RUNPOD_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

GPU_MAPPING = {
    "AMD Radeon Instinct MI300X": "MI300X",
    "NVIDIA A100 80GB PCle": "A100 PCIe",
    "NVIDIA A100 80GB SXM": "A100 SXM",
    "NVIDIA A30 PCIe": "A30",
    "NVIDIA A40 PCIe": "A40",
    "NVIDIA B200 SXM 192 GB": "B200",
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

def process_runpod_prices(gpu_rows):
    runpod.api_key = RUNPOD_KEY

    # Get all available GPUs from RunPod
    available_gpus = runpod.get_gpus()
    runpod_prices = {}
    for gpu in available_gpus:
        gpu_id = gpu["id"]
        gpu_info = runpod.get_gpu(gpu_id)
        runpod_prices[gpu["displayName"]] = gpu_info.get("securePrice")

    updates = []
    now = datetime.now().isoformat()

    for db_row in gpu_rows:
        db_name = db_row['gpu_name']
        runpod_name = GPU_MAPPING.get(db_name)
        if not runpod_name:
            print(f"No RunPod mapping for DB GPU: {db_name}")
            continue

        secure_price = runpod_prices.get(runpod_name)
        if secure_price is None:
            print(f"No RunPod price found for: {runpod_name}")
            continue

        # Fetch existing JSONB or start new
        runpod_jsonb = db_row.get("runpod") or {}
        runpod_jsonb[now] = secure_price

        updates.append({
            "id": db_row['id'],
            "runpod": runpod_jsonb
        })

    # Batch update using upsert
    if updates:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase.table('gpu-price-tracker').upsert(updates).execute()
        print(f"Batch updated {len(updates)} rows with RunPod prices.")
    else:
        print("No updates to perform.")

if __name__ == "__main__":
    process_runpod_prices()