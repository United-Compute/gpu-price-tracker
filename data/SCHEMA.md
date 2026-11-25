# Data schema (version 1)

Generated from `schema.json`. The same field names are used by the API at https://unitedcompute.ai/api/v1.

- **prices**: USD per GPU per hour, for one GPU (single-GPU offers only). Other currencies are converted when collected.
- **timestamps**: ISO 8601 in UTC, e.g. 2026-11-25T12:00:00Z.
- **csv**: Empty cell = null. Booleans are true/false. `regions` is a JSON array in a text cell.
- **parquet**: Same columns and order as the CSV. `regions` is a JSON text column.

## `offers`

Current state: one row per offer (cloud x GPU product x cloud type x pricing). Rows are kept when an offer is sold out or disappears, so check `in_stock` and `fresh`.

Files: `offers.csv`, `offers.parquet`, `offers.json`

API: `/api/v1/offers`

| Field | Type | Description |
|---|---|---|
| `offer_id` | string | Stable id of the offer: cloud, the cloud's own product id, tier and pricing. Joins `offers`, `price_changes` and `daily_prices`. |
| `gpu_id` | string | Canonical GPU id, e.g. h100-sxm-80gb (see `gpus`). |
| `gpu_name` | string | GPU name, e.g. H100 SXM. |
| `vendor` | string | NVIDIA, AMD, ... |
| `vram_gb` | integer, nullable | GPU memory in GB. |
| `provider_id` | string | Cloud id, e.g. runpod (see `clouds`). |
| `provider_name` | string | Cloud name, e.g. RunPod. |
| `provider_url` | string, nullable | Where to rent it. |
| `reseller` | boolean | true if the cloud resells other clouds' GPUs. |
| `via` | string, nullable | Platform the data comes through, e.g. Shadeform; null if read from the cloud directly. |
| `cloud_type` | string | datacenter (the cloud's own or partner data centers) or community (marketplace hosts). |
| `pricing` | string | on_demand or spot. |
| `currency` | string | Always USD. |
| `gpu_count` | integer | Always 1: prices are for a single GPU. |
| `price_per_hour` | number, nullable | Price you can rent at now; null if sold out or not fresh. |
| `list_price_per_hour` | number, nullable | Advertised price, which may not be available. |
| `in_stock` | boolean, nullable | Rentable at the last check; null if not fresh. |
| `stock_level` | string, nullable | low, medium, high or available (cloud reports no level); null if not reported or not fresh. |
| `regions` | json | Where it is in stock: array of {id, location, stock}. id is a data center id or a 2-letter country code. Empty if not reported or not fresh. |
| `checked_at` | timestamp | Last time the collector saw this offer. |
| `changed_at` | timestamp | Last time its price or stock changed. |
| `first_seen_at` | timestamp | When the collector first saw this offer. |
| `fresh` | boolean | Checked within the last 2 hours. Offers that are not fresh have no current price or stock. |

## `price_changes`

Full history: one row each time an offer's price, stock or regions changed (checked every 15 minutes). The state holds until the next row for the same offer_id.

Files: `history/YYYY/MM/YYYY-MM-DD.csv.gz`, `price_changes.parquet`

| Field | Type | Description |
|---|---|---|
| `observed_at` | timestamp | When the change was seen. |
| `offer_id` | string | See `offers`. |
| `gpu_id` | string | See `offers`. |
| `provider_id` | string | See `offers`. |
| `cloud_type` | string | See `offers`. |
| `pricing` | string | See `offers`. |
| `price_per_hour` | number, nullable | Rentable price from this moment; null if sold out. |
| `list_price_per_hour` | number, nullable | Advertised price. |
| `in_stock` | boolean, nullable | Rentable from this moment. |
| `stock_level` | string, nullable | See `offers`. |
| `regions` | json | See `offers`. |

## `daily_prices`

One row per offer and finished UTC day, computed from price_changes (time-weighted). Use this for charts and averages.

Files: `daily_prices.csv`, `daily_prices.parquet`

| Field | Type | Description |
|---|---|---|
| `date` | date | UTC day. |
| `offer_id` | string | See `offers`. |
| `gpu_id` | string | See `offers`. |
| `provider_id` | string | See `offers`. |
| `cloud_type` | string | See `offers`. |
| `pricing` | string | See `offers`. |
| `price_min` | number, nullable | Lowest rentable price that day; null if never in stock. |
| `price_max` | number, nullable | Highest rentable price that day. |
| `price_avg` | number, nullable | Average rentable price, weighted by time in stock. |
| `list_price_per_hour` | number, nullable | Advertised price at the end of the day. |
| `in_stock_share` | number | Share of the day (0-1) the offer was rentable, counted from when it was first seen. |

## `index_daily`

United Compute GPU Price Index, daily: median across clouds of each cloud's cheapest rentable on-demand price for one GPU (resellers excluded). Method: https://unitedcompute.ai/gpu-price-index#methodology

Files: `index_daily.csv`, `index_daily.parquet`

| Field | Type | Description |
|---|---|---|
| `date` | date | UTC day (finished days only). |
| `index` | string | Index id, e.g. h100. |
| `ticker` | string | e.g. UC-H100. |
| `gpu_id` | string | See `gpus`. |
| `close` | number, nullable | Index value at the end of the day. |
| `high` | number, nullable | Highest hourly value that day. |
| `low` | number, nullable | Lowest hourly value that day. |
| `clouds` | integer, nullable | Clouds in the index at the close. |

## `clouds`

Clouds the collector reads.

Files: `clouds.csv`, `clouds.parquet`

API: `/api/v1/providers`

| Field | Type | Description |
|---|---|---|
| `id` | string | Cloud id (provider_id elsewhere). |
| `name` | string | Cloud name. |
| `url` | string, nullable | Website or pricing page. |
| `marketplace` | boolean | true for marketplaces, where hosts list their own machines. |
| `reseller` | boolean | See `offers`. |
| `via` | string, nullable | See `offers`. |
| `added_at` | timestamp | When the collector started reading this cloud. |

## `gpus`

GPU catalog.

Files: `gpus.csv`, `gpus.parquet`

API: `/api/v1/gpus`

| Field | Type | Description |
|---|---|---|
| `id` | string | Canonical GPU id (gpu_id elsewhere). |
| `name` | string | GPU name. |
| `vendor` | string | NVIDIA, AMD, ... |
| `vram_gb` | integer, nullable | GPU memory in GB. |
| `class` | string, nullable | datacenter, workstation or consumer. |
| `form_factor` | string, nullable | SXM, PCIe, ... |

License: CC BY 4.0. Attribution: United Compute, https://unitedcompute.ai
