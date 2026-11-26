# United Compute GPU price API

Live reference for the `gpu-prices` skill. Prices move. Call the API or the MCP tool; do not reuse numbers from memory or from this file.

- Site: https://unitedcompute.ai
- Human docs: https://unitedcompute.ai/api
- Agent map: https://unitedcompute.ai/llms.txt
- OpenAPI (offers, GPUs, providers only): https://unitedcompute.ai/openapi.json
- Tracker as markdown: https://unitedcompute.ai/gpu-price-tracker.md
- MCP: `https://unitedcompute.ai/mcp`
- No API key. CORS allows any origin. Data license [CC BY 4.0](https://unitedcompute.ai/api); credit United Compute and link the site.

The collector checks each offer about every 15 minutes. `updated_at` is the last successful run. `stale: true` means that run is more than 60 minutes old (offers, GPUs, and the index). `GET /api/v1/providers` does not include `stale`.

A 503 body is `{"error":"The GPU index is temporarily unavailable. Try again in a minute."}` (the index endpoint says `"index temporarily unavailable"`). Retry once.

## What one row is

One offer is a single GPU (`gpu_count` is always 1) at one cloud, for one `cloud_type` and one `pricing`. Prices are USD per GPU-hour, tax not included.

Not in the index: multi-GPU-only machines, reserved or committed contracts, serverless.

`gpu` matching (offers, GPUs, and MCP) is case-insensitive. Separators are ignored, then the query is a substring of the id or the name. Several queries can be comma-separated. `h100` matches H100 SXM, H100 PCIe, and H100 NVL. An exact catalog id such as `h100-sxm-80gb` matches only that model. `h200` also matches `gh200-96gb`; pass `h200-sxm` or `h200-sxm-141gb` when you mean the H200.

Stable ids look like `h100-sxm-80gb`, `h200-sxm-141gb`, `b200-sxm-180gb`, `b300-sxm-288gb`, `rtx-4090-24gb`, `rtx-5090-32gb`. Filter memory with `vram_gb` / `min_vram`, not the suffix on the id.

## REST

### GET /api/v1/offers

Cheapest first unless `sort=vram` (most memory, then cheaper).

| Parameter | Values | Default | Meaning |
|---|---|---|---|
| `gpu` | id or name fragment, commas ok | all | See matching above. |
| `vendor` | `nvidia`, `amd` (any case) | all | GPU vendor. |
| `provider` | cloud id or name, commas ok | all | `runpod,lambda`. Matches `provider_id` or `provider_name`. Ids are lowercase (`vast`, `runpod`). |
| `cloud_type` | `datacenter`, `community` | all | Own data centers, or marketplace hosts. The value `secure` is not accepted; that is an internal name for datacenter. |
| `pricing` | `on_demand`, `spot`, `any` | `on_demand` | Spot is cheaper and interruptible. |
| `region` | see below | all | In stock in that place. Any one region on the offer is enough. |
| `min_vram` | number, GB | none | Minimum `vram_gb`. |
| `max_price` | number, USD | none | Keeps rows whose `price_per_hour` is set and `<=` this. Rows with a null price never match. |
| `in_stock` | `true`, `false`, `any` (`all` is the same as `any`) | `true` | `true`: rentable now. `false`: not rentable (sold out, no current price, or a stale check). |
| `exclude_resellers` | `true` or anything else | false | `true` drops `reseller` clouds and offers read `via` a reseller. |
| `sort` | `price`, `vram` | `price` | |
| `limit` | integer 1–1000 | 100 | |

Rentable means all of: `fresh` (checked within 2 hours), `in_stock` is not false, `price_per_hour` is not null. A cloud that does not publish a stock flag can still be rentable (`in_stock: null`) when the check is fresh and a price is set.

Envelope: `updated_at`, `stale`, `count`, `offers`.

Offer fields:

| Field | Meaning |
|---|---|
| `offer_id` | `provider\|product\|tier\|pricing`. Joins the open dataset's price history. |
| `gpu_id`, `gpu_name`, `vendor`, `vram_gb` | Model. `vram_gb` may not equal the number in the id. |
| `provider_id`, `provider_name`, `provider_url` | Cloud, and where to rent. |
| `reseller`, `via` | Resells other clouds, or the price was read through that reseller. |
| `cloud_type` | `datacenter` or `community`. |
| `pricing` | `on_demand` or `spot`. |
| `currency` | `USD`. |
| `gpu_count` | `1`. |
| `price_per_hour` | What you pay now. Null if not rentable. |
| `list_price_per_hour` | Advertised price. Kept even when the offer is not fresh. |
| `in_stock` | Current availability. Null when the cloud omits it or the check is stale. |
| `stock_level` | `low`, `medium`, `high`, `available`, or null. |
| `regions` | `{id, location, stock}` for places in stock. Empty when the check is stale. |
| `checked_at`, `changed_at`, `first_seen_at` | ISO 8601. Last check, last price or stock change, first time we saw the offer. |
| `fresh` | Checked within 2 hours. If false, price, stock, stock level, and regions are cleared. |

```bash
curl -sS "https://unitedcompute.ai/api/v1/offers?gpu=h100&max_price=3&limit=5"
curl -sS "https://unitedcompute.ai/api/v1/offers?gpu=h100-sxm-80gb&region=US&cloud_type=datacenter&exclude_resellers=true&limit=5"
curl -sS "https://unitedcompute.ai/api/v1/offers?gpu=rtx-4090&pricing=spot&limit=5"
curl -sS "https://unitedcompute.ai/api/v1/offers?gpu=rtx-5090&cloud_type=community&limit=5"
curl -sS "https://unitedcompute.ai/api/v1/offers?gpu=b200&pricing=any&cloud_type=datacenter&limit=5"
curl -sS "https://unitedcompute.ai/api/v1/offers?provider=runpod,lambda&gpu=h100&limit=5"
curl -sS "https://unitedcompute.ai/api/v1/gpus?min_vram=80&in_stock=true"
curl -sS "https://unitedcompute.ai/api/v1/index?index=h100"
curl -sS "https://unitedcompute.ai/api/v1/providers"
```

Each of those returned HTTP 200 against the live API when this skill was written.

### Region matching

The comparison is case-insensitive. The server works out a country for each region on an offer, from the region id (`DE`), its `location` text (`Des Moines, IA, United States`), or the parts of the id (`desmoines-usa-1`, `de/fra/2`, `EU-CZ-1`, `us-east-1`). The filter then compares against that country.

- **Country:** an ISO code or an English name. `region=DE` and `region=Germany` are the same. `US` matches `us-east-1`, `US Central 1` and `desmoines-usa-1`.
- **Area:** `Europe` (alias `eu`), `North America` (`na`; the alias `usa` is North America, not only the US), `Asia` (`apac`, includes the Middle East), `Oceania`, `South America` (`latam`), `Africa`. Some regions only name an area, with no country (`eu-west`, `EU North 1`, `asia-pacific`). They match the area but no country.
- **Anything else:** an exact region id (`fr-par-2`), or text in the region's id or `location`, so a city name works (`Frankfurt`, `Paris`).

An offer matches when any one of its regions matches. Its `regions` list still shows all of them, so read it before you name a location to the user.

### GET /api/v1/gpus

One row per model. Order is a fixed popularity list, then more VRAM, then name. On-demand offers only, except the spot column.

Parameters: `gpu`, `vendor`, `min_vram`, `in_stock`. There is no `limit`. `in_stock` is not filtered unless you pass `true` (models you cannot rent right now stay in the list, with null prices). MCP `list_gpus` does the opposite: `in_stock_only` defaults to true.

| Field | Meaning |
|---|---|
| `id`, `name`, `vendor`, `vram_gb` | Model. |
| `class` | `datacenter`, `workstation`, `consumer`, or null. |
| `form_factor` | `SXM`, `PCIe`, and similar. |
| `cheapest_price_per_hour` | Cheapest rentable on-demand price, any cloud. |
| `cheapest_provider_id` | Cloud that price is from. |
| `cheapest_datacenter_price_per_hour` | Cheapest rentable on-demand data-center price. |
| `cheapest_community_price_per_hour` | Cheapest rentable on-demand community price. |
| `cheapest_spot_price_per_hour` | Cheapest rentable spot price, any cloud type. |
| `offers_in_stock` | Rentable **on-demand** offers. |
| `offers_total` | On-demand offers we track, including ones you cannot rent now. |
| `providers_in_stock` | Distinct clouds with a rentable on-demand offer. |

`offers_in_stock` on a **provider** counts spot as well. On a **GPU** it does not.

### GET /api/v1/providers

No query parameters. Envelope: `updated_at`, `count`, `providers` (no `stale`).

| Field | Meaning |
|---|---|
| `id`, `name`, `url` | Cloud. |
| `marketplace` | The cloud runs a marketplace. Independent of each offer's `cloud_type`: a marketplace can still have `datacenter` offers. |
| `reseller` | Resells other clouds' GPUs. |
| `via` | We read this cloud through that reseller, usually Shadeform. Prices are the reseller's. |
| `added_at` | When we started tracking it. |
| `offers_in_stock` | Rentable offers, on-demand and spot. |
| `offers_total` | Offers we track for this cloud. |

Clouds with no offers are omitted. Names are alphabetical.

### GET /api/v1/index

Not listed in `openapi.json`. It is a live route.

| Parameter | Values |
|---|---|
| `index` | `h100`, `h200`, `b200`, `b300`, `a100`, `rtx-5090`. Omit it for all six. |
| `history` | `hourly` or `daily`. Omit it for the current value only. |

An unknown `index` is HTTP 400: `{"error":"unknown index '…'","indexes":["h100","h200","b200","b300","a100","rtx-5090"]}`.

The value is the median, across clouds, of each cloud's cheapest rentable on-demand price for one specific GPU (`h100` is `h100-sxm-80gb`, not every H100). Resellers are excluded. The headline needs at least 5 clouds. `datacenter` and `marketplace` are the same median inside that type and need at least 3 clouds (`marketplace` is the community sub-index). Method version is in `method_version`. `license` on the body is CC BY 4.0.

Per index: `index`, `ticker` (`UC-H100`, `UC-H200`, `UC-B200`, `UC-B300`, `UC-A100`, `UC-5090`), `gpu_id`, `gpu_name`, `value`, `datacenter`, `marketplace`, `clouds`, `change_24h`, `change_7d`, `constituents`, `excluded`, `url`.

`change_24h` and `change_7d` are fractions (current / past − 1), not dollars. `change_7d` is null until seven days of history exist. Constituents are `{provider_id, provider_name, type, price_per_hour}` with `type` of `datacenter` or `marketplace`. `excluded` gives a reason: `Reseller`, `Sold out`, or `No fresh data`.

`history=daily` adds `daily`: newest day first, `{date, close, high, low, clouds}`. `history=hourly` adds `hourly`: oldest first, `{t, value, datacenter, marketplace, clouds}`. Daily history can be long; ask for it only when the user wants a trend.

Pages: `https://unitedcompute.ai/gpu-price-index/<index>`.

## GPU page URLs

`https://unitedcompute.ai/gpu-price-tracker/<slug>`

Slug: drop a trailing `-<digits>gb` from `gpu_id`, unless two catalog ids would shorten to the same string. Current collisions, which keep the full id:

- `a100-sxm-40gb`, `a100-sxm-80gb` (`a100-sxm` is a 404)
- `a100-pcie-*`
- `v100-sxm-*`, `v100-pcie-*`

So `h100-sxm-80gb` → `/gpu-price-tracker/h100-sxm`, `h200-sxm-141gb` → `/gpu-price-tracker/h200-sxm`, `b200-sxm-180gb` → `/gpu-price-tracker/b200-sxm`, `rtx-4090-24gb` → `/gpu-price-tracker/rtx-4090`, `rtx-5090-32gb` → `/gpu-price-tracker/rtx-5090`. Opening the full id redirects to the short slug.

## MCP

The server is served at `https://unitedcompute.ai/mcp`. Its name is `united-compute`. The same connect command is already on the API docs and the tracker agent view: `claude mcp add --transport http united-compute https://unitedcompute.ai/mcp`. `.mcp.json` at the repo root is that command checked in. There is no second MCP config.

Streamable HTTP. Stateless. No session id and no `initialize` required before `tools/call`, though a normal client will initialize. Protocol versions the server accepts: `2025-06-18`, `2025-03-26`, `2024-11-05`.

```bash
curl -sS https://unitedcompute.ai/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"example","version":"0"}}}'
```

```bash
curl -sS https://unitedcompute.ai/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_gpu_offers","arguments":{"gpu":"h100","max_price":3,"cloud_type":"datacenter","limit":5}}}'
```

`GET https://unitedcompute.ai/mcp` is HTTP 405 with `Allow: POST, OPTIONS` and a one-line plain-text hint. A client that only speaks SSE will not connect. Use Streamable HTTP.

A JSON-RPC notification (no `id`) gets HTTP 202 and an empty body. The success body is JSON, not an event stream: `{jsonrpc, id, result}` where `result.content[0].text` is a JSON string and `result.structuredContent` is the same object.

Tool results add `source` (`https://unitedcompute.ai/gpu-price-tracker`), `updated_at`, `stale`, and `unit` (`USD per GPU-hour, 1 GPU`).

`search_gpu_offers` uses the offers filters, with these differences:

| MCP argument | REST equivalent |
|---|---|
| `include_unavailable: true` | `in_stock=any` |
| omitted (default) | `in_stock=true` |
| `limit` default 20, values above 200 are capped to 200 | default 100, max 1000 |
| `exclude_resellers` is a JSON boolean | query string `true` |

Each offer in the tool result is compact: `gpu`, `gpu_id`, `vram_gb`, `cloud`, `via` or `reseller`, `cloud_type`, `pricing`, `price_per_hour`, `list_price_per_hour` only when the current price is null, `in_stock`, `stock`, `regions` (up to 8 strings like `France (FR)`), `more_regions`, `rent_url`, `checked_at`.

`get_gpu` with `H100` returns `note` and `matches` (`id`, `name`, `vram_gb`) instead of offers. Call again with one `id`. One match returns `gpu` plus `offers_in_stock` and `offers_not_available`.

`list_gpus` returns the same GPU objects as `GET /api/v1/gpus`. `list_providers` returns the same provider objects as `GET /api/v1/providers`.

Server name: `united-compute`.

## Helper script

`scripts/gpu-prices.py` (Python 3, no packages) calls the REST API and prints a markdown table, or the raw JSON with `--json`.

```bash
python3 scripts/gpu-prices.py offers --gpu h100 --max-price 3 --limit 5
python3 scripts/gpu-prices.py offers --gpu h100-sxm-80gb --region US --cloud-type datacenter --exclude-resellers --limit 5
python3 scripts/gpu-prices.py offers --gpu rtx-4090 --pricing spot --limit 5
python3 scripts/gpu-prices.py gpus --min-vram 80 --in-stock true
python3 scripts/gpu-prices.py index --index h100
python3 scripts/gpu-prices.py providers
```

## Bulk history

The API is the current state, plus index history when you pass `history`. Every price and stock change, daily per-offer prices, and the index are the open dataset, same field names, updated daily:

- https://github.com/United-Compute/gpu-price-tracker
- https://huggingface.co/datasets/united-compute/gpu-prices
- https://www.kaggle.com/datasets/maxhager/gpu-cloud-prices
