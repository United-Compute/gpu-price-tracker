# GPU Price Tracker: open data

Live GPU rental prices **and availability** across 59 clouds, from the
[United Compute GPU price tracker](https://unitedcompute.ai/gpu-price-tracker).

Most GPU price lists show what a cloud *charges*. This dataset records what you can actually
*rent right now*: every 15 minutes, for every single-GPU offer, the list price, whether it is in
stock, where, and the price you would really pay.

**Browse it live:** [unitedcompute.ai/gpu-price-tracker](https://unitedcompute.ai/gpu-price-tracker)

## Files

All in [`data/`](data), updated once a day.

| File | What |
|---|---|
| [`offers.csv`](data/offers.csv) / [`offers.json`](data/offers.json) | Current state: one row per cloud × GPU × tier × pricing |
| `history/YYYY/MM/YYYY-MM-DD.csv.gz` | Full history: one row every time a price or availability changed, one file per UTC day |
| [`clouds.csv`](data/clouds.csv) | The clouds, with links, and whether they are marketplaces or resellers |
| [`gpus.csv`](data/gpus.csv) | GPU catalog: canonical id, name, vendor, VRAM, class, form factor |

### Columns (`offers.csv`)

| Column | Meaning |
|---|---|
| `cloud`, `cloud_name` | Cloud id and name |
| `gpu`, `gpu_name`, `vendor`, `vram_gb` | Canonical GPU id (same chip = same id across clouds) |
| `tier` | `secure` (data centers) or `community` (individual / third-party hosts) |
| `pricing` | `on_demand`, or `spot` (cheaper, can be stopped by the provider; "interruptible") |
| `list_price` | Advertised price, USD per GPU-hour |
| `price_now` | What you can rent it at right now, USD per GPU-hour; empty = not rentable now |
| `in_stock` | Whether a single GPU can be started right now |
| `stock` | `low` / `medium` / `high` where the cloud publishes counts |
| `regions` | JSON: data centers or countries where it is in stock right now, with their level |
| `last_checked_at`, `last_changed_at`, `first_seen_at` | UTC timestamps |
| `reseller`, `via` | `reseller`: the cloud resells other clouds' GPUs. `via`: read through a reseller (prices are the reseller's) |

The history files have the same price and availability columns plus `observed_at`.

Rules: single GPU (1x) only; prices converted to USD and without VAT; marketplaces have no list
price, so their price is the cheapest free machine and the stock level comes from the number of
free machines (1–2 low, 3–9 medium, 10+ high).

## License

[CC BY 4.0](LICENSE). Use it for anything, including commercially, as long as you credit
**United Compute** with a link to <https://unitedcompute.ai/gpu-price-tracker>.

## Contact

Missing a cloud, spotted wrong data, or want to sponsor the tracker?
Open an issue.
