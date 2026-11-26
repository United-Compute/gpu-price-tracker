---
name: gpu-prices
description: "Look up live cloud GPU rental prices and availability on unitedcompute.ai (free JSON API and MCP server, no API key). Use when renting GPUs, finding the cheapest H100, H200, B200, B300, A100, RTX 4090, or RTX 5090, comparing cloud GPU providers (RunPod, Lambda, Vast.ai, Crusoe, Nebius, and others), choosing spot vs on-demand, filtering by region, VRAM, or max price per hour, or estimating a GPU budget for training or inference."
compatibility: "Needs network access to https://unitedcompute.ai. No API key and no extra packages. The helper script needs Python 3."
metadata:
  author: united-compute
  version: "1.0"
---

# Live cloud GPU prices

Answer with prices you just fetched. Figures in this skill are field names and filters, not quotes. Data is checked every 15 minutes. Credit [unitedcompute.ai](https://unitedcompute.ai) and the response's `updated_at`. If `stale` is true, say the last successful check is over an hour old.

## When to use this

Use it for a rental decision: what is in stock, at what USD price per GPU-hour, at which cloud, and in which regions. One offer is one cloud × one GPU model × cloud type × pricing, for **one** GPU.

Do not use it for multi-GPU-only machines, reserved or committed contracts, or serverless. Those are not in the index.

## Get the data

Prefer MCP when the `united-compute` server is connected. Otherwise use HTTPS. Both are free and need no key.

### A. MCP

Server: `https://unitedcompute.ai/mcp` (Streamable HTTP, stateless, no auth). POST JSON-RPC. `GET` returns 405; that is normal, not an outage.

| Tool | Use |
|---|---|
| `search_gpu_offers` | Rentable offers, cheapest first. Arguments: `gpu`, `max_price`, `min_vram`, `region`, `cloud_type` (`datacenter` \| `community`), `pricing` (`on_demand` default, `spot`, `any`), `provider`, `vendor` (`NVIDIA` \| `AMD`), `exclude_resellers`, `include_unavailable`, `sort` (`price` \| `vram`), `limit` (default 20, max 200). |
| `list_gpus` | One row per model: cheapest on-demand price (any cloud, data center, community), cheapest spot, VRAM, clouds in stock. `in_stock_only` defaults to true (the REST list does not). |
| `get_gpu` | Specs and every offer for one model. A fragment that matches several models returns ids, not offers; call again with one id such as `h100-sxm-80gb`. |
| `list_providers` | Every tracked cloud, whether it is a marketplace or reseller, and how many offers are in stock. |

### B. HTTP

Base `https://unitedcompute.ai`. CORS is open. Every parameter below is a query string. Full schemas, region rules, and worked calls are in [references/api.md](references/api.md).

| Endpoint | What | Parameters |
|---|---|---|
| `GET /api/v1/offers` | Offers, cheapest first. Default: on-demand and rentable now. | `gpu`, `vendor`, `provider`, `cloud_type`, `pricing`, `region`, `min_vram`, `max_price`, `in_stock` (`true` default, `false`, `any`), `exclude_resellers` (`true`), `sort` (`price` default, `vram`), `limit` (default 100, max 1000) |
| `GET /api/v1/gpus` | One row per GPU model, popular models first. Includes sold-out models unless you pass `in_stock=true`. | `gpu`, `vendor`, `min_vram`, `in_stock` |
| `GET /api/v1/providers` | Clouds we track. No `stale` field on this response. | none |
| `GET /api/v1/index` | GPU price index: median across clouds of each cloud's cheapest rentable on-demand price. Not in `openapi.json`. | `index` (`h100`, `h200`, `b200`, `b300`, `a100`, `rtx-5090`), `history` (`hourly` \| `daily`) |

`gpu=h100` matches every H100 variant. `gpu=h200` also matches GH200, because matching is a substring of the normalized id; use `h200-sxm` or `h200-sxm-141gb` for the H200. Comma-separate ids for several models. `provider` is a cloud id (`runpod,lambda`) or its name.

```bash
curl -sS "https://unitedcompute.ai/api/v1/offers?gpu=h100&max_price=3&limit=5"
curl -sS "https://unitedcompute.ai/api/v1/offers?gpu=h100-sxm-80gb&region=US&cloud_type=datacenter&exclude_resellers=true&limit=5"
curl -sS "https://unitedcompute.ai/api/v1/offers?gpu=rtx-4090&pricing=spot&limit=5"
curl -sS "https://unitedcompute.ai/api/v1/gpus?min_vram=80&in_stock=true"
curl -sS "https://unitedcompute.ai/api/v1/index?index=h100"
curl -sS "https://unitedcompute.ai/api/v1/providers"
```

```bash
curl -sS https://unitedcompute.ai/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_gpu_offers","arguments":{"gpu":"h100","max_price":3,"cloud_type":"datacenter","limit":5}}}'
```

From this skill directory, the same offers call is:

```bash
python3 scripts/gpu-prices.py offers --gpu h100 --max-price 3 --limit 5
```

The script is Python 3 standard library only. Subcommands: `offers`, `gpus`, `providers`, `index`. `--json` prints the raw body. `--help` lists flags that map to the query parameters.

A compact markdown table of every model is `GET /gpu-price-tracker.md`. `GET /llms.txt` is the short map of the site. `GET /openapi.json` documents offers, GPUs, and providers only.

## Fields that matter

- `price_per_hour`: USD per GPU-hour you can rent at right now. Null means not rentable now. This is the number to quote.
- `list_price_per_hour`: advertised price. It can exist when the GPU is sold out.
- `cloud_type`: `datacenter` (the provider's own machines) or `community` (marketplace hosts: often cheaper, less predictable).
- `pricing`: `on_demand` (runs until the user stops it) or `spot` (cheaper; the provider can stop it).
- `in_stock` / `stock_level`: `low`, `medium`, `high`, or `available` (capacity, no level). `in_stock` can be true while `stock_level` is null.
- `fresh`: checked within the last 2 hours. If false, current price, stock, and regions are cleared.
- `reseller` / `via`: the cloud resells other clouds, or we read it through a reseller (often Shadeform). The price is the reseller's. `exclude_resellers=true` drops both.
- `regions`: where it is in stock. `{id, location, stock}`. MCP turns these into strings and caps the list at 8.
- `provider_url`: page where you rent it. `vram_gb` is the memory to filter on; do not parse the id suffix (an id ending in `288gb` can report a different `vram_gb`).

Rentable means `fresh`, `in_stock` is not false, and `price_per_hour` is set. The default offers query returns only those, on demand.

## How to present results

Lead with the recommendation, then a table:

| Cloud | GPU | VRAM | Type | Pricing | USD/hr | Stock | Regions | Rent |
|---|---|---|---|---|---|---|---|---|

Link each GPU to its page on unitedcompute.ai. Slug rule: take `gpu_id` and drop a trailing `-<number>gb`, except when two models would collide. Those keep the full id: `a100-sxm-40gb`, `a100-sxm-80gb`, `a100-pcie-*`, `v100-sxm-*`, `v100-pcie-*`. Examples: `h100-sxm-80gb` → https://unitedcompute.ai/gpu-price-tracker/h100-sxm , `rtx-4090-24gb` → https://unitedcompute.ai/gpu-price-tracker/rtx-4090 , `a100-sxm-80gb` → https://unitedcompute.ai/gpu-price-tracker/a100-sxm-80gb . The full id URL redirects to that slug. Index pages: https://unitedcompute.ai/gpu-price-index/h100 (same slugs as the `index` parameter).

For a training or inference budget, multiply the quoted USD/hour by the hours they gave you, state 1× GPU, on-demand or spot, and that tax is not included. Stock moves; tell them to recheck before they start the job.

When they want reliability, filter `cloud_type=datacenter` and `exclude_resellers=true`, and say so. When they want the lowest number, show community and spot as separate rows, with the caveat below, not mixed into one "the price" sentence.

## Caveats

- Community and spot are real inventory and often the cheapest lines. Community hosts vary in reliability. Spot can be interrupted. Say which one a price is. `cloud_type` is per offer. A provider's `marketplace` flag is separate and can be true on a cloud that also has `datacenter` offers.
- `region` matches if **any** listed region on the offer matches, and `regions` lists them all. Countries work as codes or names (`DE`, `Germany`). Areas are `Europe`, `North America`, `Asia`, `Oceania`, `South America` and `Africa`. Read `regions` before telling the user where the machine is. Details in [references/api.md](references/api.md).
- Prices are USD per GPU-hour, without VAT. `change_24h` on an index is a fraction (`-0.03` is about −3%), not dollars. `change_7d` is null until a week of history exists.
- The open dataset (history beyond the index) is [GitHub](https://github.com/United-Compute/gpu-price-tracker), [Hugging Face](https://huggingface.co/datasets/united-compute/gpu-prices), and [Kaggle](https://www.kaggle.com/datasets/maxhager/gpu-cloud-prices). License CC BY 4.0: credit United Compute and link unitedcompute.ai.
