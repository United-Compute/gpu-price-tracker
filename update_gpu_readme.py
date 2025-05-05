from supabase import create_client
import matplotlib.pyplot as plt
from datetime import datetime
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

README_PATH = "README.md"
CHARTS_DIR = "price_history_charts"

def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', name)

def fetch_all_gpus():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = supabase.table('gpu-price-tracker').select('*').execute()
    if not response.data:
        raise ValueError("No GPUs found in the database.")
    return response.data

def get_latest_market_price(price_history):
    if not price_history or not price_history.get('prices'):
        return ""
    prices_dict = price_history['prices']
    if not prices_dict:
        return ""
    latest_date = max(prices_dict.keys())
    latest_price = prices_dict[latest_date]
    return f"${latest_price:,.2f}"

def plot_price_history(gpu_name, price_history, output_path):
    if not price_history or not price_history.get('prices'):
        print(f"No price history for {gpu_name}, skipping.")
        return
    prices_dict = price_history['prices']
    dates = [datetime.fromisoformat(d) for d in prices_dict.keys()]
    prices = [prices_dict[d] for d in prices_dict.keys()]
    if not dates or not prices:
        print(f"No valid price data for {gpu_name}, skipping.")
        return
    sorted_pairs = sorted(zip(dates, prices))
    dates, prices = zip(*sorted_pairs)
    plt.figure(figsize=(16, 6), dpi=200)
    plt.plot(dates, prices, marker='o', markersize=8, linewidth=3)
    plt.title(f"Price History for {gpu_name}", fontsize=20)
    plt.xlabel("Date", fontsize=16)
    plt.ylabel("Price (USD)", fontsize=16)
    plt.tick_params(axis='x', labelsize=12)
    plt.tick_params(axis='y', labelsize=12)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved price history graph to {output_path}")

def generate_table_rows(gpus):
    rows = []
    for gpu in gpus:
        filename = sanitize_filename(gpu.get('gpu_name', '')) + ".png"
        chart_url = f"https://raw.githubusercontent.com/yachty66/gpu-price-tracker/main/price_history_charts/{filename}"
        rows.append(f"""  <tr>
    <td>{gpu.get('gpu_name', '')}</td>
    <td>{get_latest_market_price(gpu.get('price_history', {}))}</td>
    <td>
      <a href="{chart_url}">
        <img src="{chart_url}" alt="Price History" style="display:block;margin:auto;">
        <div style="font-size:10px; color:#888; text-align:center;">(click to see)</div>
      </a>
    </td>
    <td>{gpu.get('fp_16', '')}</td>
    <td>{gpu.get('tdp', '')}</td>
    <td>{gpu.get('fl_watt', '')}</td>
    <td>{gpu.get('fl_watt', '')}</td>
    <td>{gpu.get('vram', '')}</td>
    <td>{gpu.get('mem_bus_width', '')}</td>
    <td>{gpu.get('bandwith', '')}</td>
    <td>{gpu.get('release_date', '')}</td>
    <td><a href="{gpu.get('url', '')}">Link</a></td>
  </tr>""")
    return "\n".join(rows)

def update_readme(table_html):
    start_marker = "<!-- PRICES_START -->"
    end_marker = "<!-- PRICES_END -->"
    table_header = """<table>
  <tr>
    <th>GPU Name</th>
    <th>Market Price</th>
    <th>Price History</th>
    <th>FP16 [TFLOPS]</th>
    <th>Watt</th>
    <th>TFLOPS/$</th>
    <th>TFLOPS/Watt</th>
    <th>VRAM</th>
    <th>Bus Width</th>
    <th>Bandwidth</th>
    <th>Release Date</th>
    <th>Link</th>
  </tr>
"""
    table_footer = "</table>"
    new_table = f"{table_header}{table_html}\n{table_footer}"

    with open(README_PATH, "r") as f:
        content = f.read()
    start = content.find(start_marker)
    end = content.find(end_marker)
    if start == -1 or end == -1:
        raise ValueError("Markers not found in README.md")
    new_content = (
        content[: start + len(start_marker)]
        + "\n"
        + new_table
        + "\n"
        + content[end:]
    )
    with open(README_PATH, "w") as f:
        f.write(new_content)

def main():
    os.makedirs(CHARTS_DIR, exist_ok=True)
    gpus = fetch_all_gpus()
    # Generate and save price history charts
    for row in gpus:
        gpu_name = row['gpu_name']
        price_history = row['price_history']
        filename = sanitize_filename(gpu_name) + ".png"
        output_path = os.path.join(CHARTS_DIR, filename)
        plot_price_history(gpu_name, price_history, output_path)
    # Update README with latest table
    table_html = generate_table_rows(gpus)
    update_readme(table_html)
    print("README.md updated with latest GPU data from Supabase.")

if __name__ == "__main__":
    main()