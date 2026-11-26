# GPU Cloud Prices & Availability

Get **live cloud GPU rental prices and whether you can actually rent them**, across 59 GPU clouds,
checked every 15 minutes: RunPod, Lambda, Vast.ai, Nebius, Crusoe, Hyperstack, Verda, Lium,
CloudRift, Clore.ai and more. H100, H200, B200, B300, A100, L40S, RTX 4090, RTX 5090, MI300X and
70+ other GPU models.

Most GPU price lists show what a cloud *advertises*. This Actor returns what is **rentable right
now**: the real price, stock level and the regions that have it. Data comes from the free
[United Compute GPU Price Tracker](https://unitedcompute.ai/gpu-price-tracker?utm_source=apify&utm_medium=actor)
API. No scraping, no proxies, no API key, runs in seconds.

## What you can get

| Mode | What you get | Example |
|---|---|---|
| **Offers** (default) | Every single-GPU offer: cloud, GPU, price per hour, advertised price, stock level, regions, data center vs marketplace, on-demand vs spot | Cheapest H100 in Europe under $3/hr |
| **Cheapest per GPU** | One row per GPU model: cheapest price now (any cloud, data center, marketplace, spot) and how many clouds have it | Every GPU with 80 GB+ and its cheapest price |
| **Clouds** | The 59 clouds tracked, with offers in stock and in total | Which clouds have the most GPUs available |
| **GPU Price Index** | The United Compute GPU Price Index (median across clouds) for H100, H200, B200, B300, A100, RTX 5090, current or hourly/daily history | H100 rental price index, daily |

## Use cases

- **Find the cheapest GPU** you can rent right now for training or inference, by VRAM, region and budget.
- **Monitor GPU prices**: schedule the Actor hourly or daily and get alerts or a time series of H100 / B200 prices.
- **Compare GPU clouds** for a procurement decision or a market report.
- **Feed AI agents**: Apify exposes this Actor as a tool through its MCP server, so Claude, Cursor or ChatGPT can look up live GPU prices.

## Input examples

Cheapest rentable H100 in Europe, data centers only, under $3 per hour:

```json
{ "mode": "offers", "gpu": "h100", "region": "Europe", "cloudType": "datacenter", "maxPrice": 3 }
```

RTX 4090 and RTX 5090 spot prices:

```json
{ "mode": "offers", "gpu": "rtx-4090,rtx-5090", "pricing": "spot" }
```

B200 price index, daily history:

```json
{ "mode": "index", "index": "b200", "history": "daily" }
```

## Output

One dataset row per offer (or GPU, cloud, index point). An offer looks like this:

```json
{
  "gpu_name": "H100 SXM",
  "provider_name": "Gcore",
  "price_per_hour": 3.0949,
  "list_price_per_hour": 3.0949,
  "in_stock": true,
  "stock_level": "medium",
  "cloud_type": "datacenter",
  "pricing": "on_demand",
  "vram_gb": 80,
  "regions": [{ "id": "Sines-3", "location": "Sines, Portugal", "stock": "medium" }],
  "checked_at": "2026-11-26T15:02:19Z"
}
```

- `price_per_hour`: USD per GPU-hour you can rent at right now; `null` = not rentable now.
- `list_price_per_hour`: the advertised price (can exist while the GPU is sold out).
- All prices are for **one GPU**, in USD, without VAT. Every field is documented in the
  [schema](https://github.com/United-Compute/gpu-price-tracker/blob/main/data/SCHEMA.md).

## Pricing

The Actor only makes one HTTP request, so a run costs a fraction of a cent in Apify platform usage.
The data itself is free.

## More

- Live tracker: [unitedcompute.ai/gpu-price-tracker](https://unitedcompute.ai/gpu-price-tracker?utm_source=apify&utm_medium=actor)
- GPU Price Index: [unitedcompute.ai/gpu-price-index](https://unitedcompute.ai/gpu-price-index?utm_source=apify&utm_medium=actor)
- Same data as a free API and MCP server: [unitedcompute.ai/api](https://unitedcompute.ai/api?utm_source=apify&utm_medium=actor)
- Full price history since Nov 2026 as an open dataset: [Hugging Face](https://huggingface.co/datasets/united-compute/gpu-prices), [Kaggle](https://www.kaggle.com/datasets/maxhager/gpu-cloud-prices)

Data is CC BY 4.0: use it for anything, including commercially, with credit to United Compute.
Missing a cloud or spotted wrong data? Email max@unitedcompute.ai.
