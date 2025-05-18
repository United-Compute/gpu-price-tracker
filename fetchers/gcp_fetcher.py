import requests
from datetime import datetime

class GCPGPUPriceFetcher:
    def __init__(self):
        self.base_url = "https://cloudbilling.googleapis.com/v1"
        self.compute_service = "services/6F81-5844-456A"
        
        self.gpu_mapping = {
            "NVIDIA H100 80GB MEGA": "H100 MEGA",
            "NVIDIA A100 80GB": "A100 80GB",
            "NVIDIA A100 40GB": "A100 40GB",
            "NVIDIA L4": "L4",
            "NVIDIA T4": "T4",
            "NVIDIA V100": "V100",
            "NVIDIA Tesla P4": "P4",
            "NVIDIA Tesla P100": "P100",
            "NVIDIA B200 180GB": "B200 180GB",
            "NVIDIA H200 141GB": "H200 141GB",
            "NVIDIA H100 80GB": "H100 80GB"
        }

    def get_gpu_prices(self, api_key):
        """Fetch GPU prices from Google Cloud Platform"""
        try:
            url = f"{self.base_url}/{self.compute_service}/skus"
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
                # Only process if it's a GPU SKU
                category = sku.get('category', {})
                if category.get('resourceGroup') != 'GPU':
                    continue

                description = sku.get('description', '')
                
                # Skip if it's a commitment or reserved instance
                if any(x in description.lower() for x in ['commitment', 'reserved', 'calendar mode']):
                    continue

                # Find matching GPU from our mapping
                matching_gpu = None
                for gpu_name in self.gpu_mapping:
                    if gpu_name.lower() in description.lower():
                        matching_gpu = self.gpu_mapping[gpu_name]
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
                            
                            # Only add if it's an on-demand instance
                            if 'OnDemand' in gpu_info['usage_type']:
                                print(f"Found GPU info: {gpu_info}")
                                gpu_prices.append(gpu_info)

            return gpu_prices

        except requests.exceptions.RequestException as e:
            print(f"Error fetching GPU prices: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            return []

def main():
    api_key = ""
    fetcher = GCPGPUPriceFetcher()
    
    print("Starting GPU price fetch...")
    gpu_prices = fetcher.get_gpu_prices(api_key)
    
    # Print the results
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

if __name__ == "__main__":
    main()