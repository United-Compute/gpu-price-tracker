# GPU Price Tracker: open data

Live GPU rental prices **and availability** across 59 clouds, from the
[United Compute GPU price tracker](https://unitedcompute.ai/gpu-price-tracker).

Most GPU price lists show what a cloud *charges*. This dataset records what you can actually
*rent right now*: every 15 minutes, for every single-GPU offer, the list price, whether it is in
stock, where, and the price you would really pay.

**Browse it live:** [unitedcompute.ai/gpu-price-tracker](https://unitedcompute.ai/gpu-price-tracker)

## Files

All in [`data/`](data), updated once a day. Every table comes as CSV and Parquet.

| File | What |
|---|---|
| [`offers.csv`](data/offers.csv) / `.parquet` / [`.json`](data/offers.json) | Current state: one row per offer (cloud × GPU product × cloud type × pricing) |
| [`daily_prices.csv`](data/daily_prices.csv) / `.parquet` | Per offer and day: lowest, highest and time-weighted average rentable price, share of the day in stock. **Start here for charts.** |
| `history/YYYY/MM/YYYY-MM-DD.csv.gz`, `price_changes.parquet` | Full history: one row every time a price or availability changed (checked every 15 minutes) |
| [`index_daily.csv`](data/index_daily.csv) / `.parquet` | [GPU Price Index](https://unitedcompute.ai/gpu-price-index) daily close, high and low (H100, H200, B200, B300, A100, RTX 5090) |
| [`clouds.csv`](data/clouds.csv) / `.parquet` | The clouds, with links, and whether they are marketplaces or resellers |
| [`gpus.csv`](data/gpus.csv) / `.parquet` | GPU catalog: canonical id, name, vendor, VRAM, class, form factor |

**Every column is documented in [`data/SCHEMA.md`](data/SCHEMA.md)** (machine-readable:
[`data/schema.json`](data/schema.json)). The field names are the same as in the live
[API](https://unitedcompute.ai/openapi.json), so code written against one works with the other.
`offer_id` joins `offers`, `daily_prices` and the history.

Changes to the format are listed in [CHANGELOG.md](CHANGELOG.md).

```python
import pandas as pd
daily = pd.read_parquet("https://raw.githubusercontent.com/United-Compute/gpu-price-tracker/main/data/daily_prices.parquet")
h100 = daily[(daily.gpu_id == "h100-sxm-80gb") & (daily.pricing == "on_demand")]
print(h100.groupby("date").price_min.min())   # cheapest rentable H100 per day
```

Rules: single GPU (1x) only; prices converted to USD and without VAT; marketplaces have no list
price, so their price is the cheapest free machine and the stock level comes from the number of
free machines (1–2 low, 3–9 medium, 10+ high).

## Use it from an AI agent

The live data is also an API and an MCP server, no key needed:
[unitedcompute.ai/api](https://unitedcompute.ai/api). This repo ships a `gpu-prices` agent skill
and plugin files for Claude Code, Cursor and Codex (see [skills/README.md](skills/README.md)):

```bash
npx skills add United-Compute/gpu-price-tracker                  # skill only
claude plugin marketplace add United-Compute/gpu-price-tracker   # skill + MCP server
claude plugin install united-compute@united-compute
```

Also on [Apify](https://apify.com/unitedcompute/gpu-prices) (source in [integrations/apify](integrations/apify)) and [RapidAPI](https://rapidapi.com/maxhager28/api/gpu-cloud-prices).

## License and citation

[CC BY 4.0](LICENSE). Use it for anything, including commercially, as long as you credit
**United Compute** with a link to <https://unitedcompute.ai/gpu-price-tracker>, e.g.:

> Source: United Compute GPU Price Tracker, https://unitedcompute.ai/gpu-price-tracker (CC BY 4.0)

```bibtex
@misc{unitedcompute_gpu_prices,
  title        = {United Compute GPU Price Tracker: live GPU rental prices and availability},
  author       = {{United Compute}},
  year         = {2026},
  howpublished = {\url{https://unitedcompute.ai/gpu-price-tracker}},
  note         = {Dataset: https://github.com/United-Compute/gpu-price-tracker, CC BY 4.0}
}
```

## Contact

Missing a cloud, spotted wrong data, or want to sponsor the tracker?
Open an issue.
