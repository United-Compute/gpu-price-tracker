#!/usr/bin/env python3
"""Live cloud GPU prices from https://unitedcompute.ai. Python 3 stdlib only. No API key.

Examples:
  python3 gpu-prices.py offers --gpu h100 --max-price 3 --limit 5
  python3 gpu-prices.py offers --gpu h100-sxm-80gb --region US --cloud-type datacenter --exclude-resellers
  python3 gpu-prices.py offers --gpu rtx-4090 --pricing spot --limit 5
  python3 gpu-prices.py gpus --min-vram 80
  python3 gpu-prices.py index --index h100
  python3 gpu-prices.py providers
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://unitedcompute.ai"
# pageSlugs() keeps the memory size when two ids shorten to the same slug.
KEEP_FULL_ID = ("a100-sxm-", "a100-pcie-", "v100-sxm-", "v100-pcie-")


def page_slug(gpu_id: str) -> str:
    if gpu_id.startswith(KEEP_FULL_ID):
        return gpu_id
    return re.sub(r"-\d+gb$", "", gpu_id)


def page_url(gpu_id: str) -> str:
    return f"{BASE}/gpu-price-tracker/{page_slug(gpu_id)}"


def fetch(path: str) -> dict:
    req = urllib.request.Request(
        BASE + path,
        headers={"Accept": "application/json", "User-Agent": "united-compute-gpu-prices/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as res:
            body = res.read().decode()
    except urllib.error.HTTPError as err:
        detail = err.read().decode(errors="replace")[:500]
        print(f"HTTP {err.code} for {path}: {detail}", file=sys.stderr)
        raise SystemExit(1)
    except urllib.error.URLError as err:
        print(f"Request failed: {err.reason}", file=sys.stderr)
        raise SystemExit(1)
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        print("Response was not JSON.", file=sys.stderr)
        raise SystemExit(1)


def query(args: argparse.Namespace, names: list[tuple[str, str]]) -> str:
    params = []
    for flag, key in names:
        value = getattr(args, flag)
        if value is None or value is False:
            continue
        if value is True:
            value = "true"
        params.append((key, str(value)))
    return "?" + urllib.parse.urlencode(params) if params else ""


def cell(value) -> str:
    if value is None or value == "":
        return "—"
    return str(value).replace("|", "/").replace("\n", " ")


def money(value) -> str:
    if value is None:
        return "—"
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return text


def table(headers: list[str], rows: list[list]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell(c) for c in row) + " |")
    return "\n".join(lines)


def regions(items: list[dict], limit: int = 4) -> str:
    labels = []
    for region in items[:limit]:
        loc = region.get("location")
        ident = region.get("id")
        labels.append(f"{loc} ({ident})" if loc and loc != ident else str(ident))
    extra = len(items) - limit
    if extra > 0:
        labels.append(f"+{extra}")
    return ", ".join(labels) if labels else "—"


def header(data: dict) -> None:
    stale = data.get("stale")
    bits = [f"updated {data.get('updated_at') or 'unknown'}"]
    if stale is not None:
        bits.append(f"stale={str(stale).lower()}")
    bits.append(BASE)
    print(" · ".join(bits))
    print()


def cmd_offers(args: argparse.Namespace) -> None:
    path = "/api/v1/offers" + query(args, [
        ("gpu", "gpu"), ("vendor", "vendor"), ("provider", "provider"),
        ("cloud_type", "cloud_type"), ("pricing", "pricing"), ("region", "region"),
        ("min_vram", "min_vram"), ("max_price", "max_price"), ("in_stock", "in_stock"),
        ("exclude_resellers", "exclude_resellers"), ("sort", "sort"), ("limit", "limit"),
    ])
    data = fetch(path)
    if args.json:
        print(json.dumps(data, indent=2))
        return
    header(data)
    rows = []
    for offer in data.get("offers") or []:
        tag = "reseller" if offer.get("reseller") else (f"via {offer['via']}" if offer.get("via") else offer.get("cloud_type"))
        rows.append([
            offer.get("provider_name"),
            offer.get("gpu_name"),
            offer.get("vram_gb"),
            tag,
            offer.get("pricing"),
            money(offer.get("price_per_hour")),
            offer.get("stock_level") or ("in stock" if offer.get("in_stock") else "—"),
            regions(offer.get("regions") or []),
            page_url(offer.get("gpu_id") or ""),
        ])
    print(table(["Cloud", "GPU", "VRAM", "Type", "Pricing", "USD/hr", "Stock", "Regions", "Page"], rows))
    print()
    print(f"{data.get('count', len(rows))} offers. USD per GPU-hour, 1 GPU, before tax. Credit {BASE}.")


def cmd_gpus(args: argparse.Namespace) -> None:
    path = "/api/v1/gpus" + query(args, [
        ("gpu", "gpu"), ("vendor", "vendor"), ("min_vram", "min_vram"), ("in_stock", "in_stock"),
    ])
    data = fetch(path)
    if args.json:
        print(json.dumps(data, indent=2))
        return
    header(data)
    rows = []
    for gpu in data.get("gpus") or []:
        rows.append([
            gpu.get("name"),
            gpu.get("vram_gb"),
            money(gpu.get("cheapest_price_per_hour")),
            money(gpu.get("cheapest_datacenter_price_per_hour")),
            money(gpu.get("cheapest_community_price_per_hour")),
            money(gpu.get("cheapest_spot_price_per_hour")),
            gpu.get("providers_in_stock"),
            page_url(gpu.get("id") or ""),
        ])
    print(table(["GPU", "VRAM", "Cheapest", "Data center", "Community", "Spot", "Clouds", "Page"], rows))
    print()
    print(f"{data.get('count', len(rows))} GPUs. On-demand prices except the Spot column. Credit {BASE}.")


def cmd_providers(args: argparse.Namespace) -> None:
    data = fetch("/api/v1/providers")
    if args.json:
        print(json.dumps(data, indent=2))
        return
    header(data)
    rows = []
    for provider in data.get("providers") or []:
        kind = "marketplace" if provider.get("marketplace") else "datacenter"
        if provider.get("via"):
            kind = f"via {provider['via']}"
        elif provider.get("reseller"):
            kind = "reseller"
        rows.append([
            provider.get("name"),
            provider.get("id"),
            kind,
            provider.get("offers_in_stock"),
            provider.get("offers_total"),
            provider.get("url"),
        ])
    print(table(["Cloud", "Id", "Kind", "In stock", "Tracked", "URL"], rows))
    print()
    print(f"{data.get('count', len(rows))} clouds. Credit {BASE}.")


def pct(value) -> str:
    if value is None:
        return "—"
    return f"{value * 100:+.1f}%"


def cmd_index(args: argparse.Namespace) -> None:
    path = "/api/v1/index" + query(args, [("index", "index"), ("history", "history")])
    data = fetch(path)
    if args.json:
        print(json.dumps(data, indent=2))
        return
    header(data)
    print(data.get("method") or "")
    print()
    rows = []
    for item in data.get("indexes") or []:
        rows.append([
            item.get("gpu_name"),
            item.get("ticker"),
            money(item.get("value")),
            money(item.get("datacenter")),
            money(item.get("marketplace")),
            item.get("clouds"),
            pct(item.get("change_24h")),
            pct(item.get("change_7d")),
            item.get("url"),
        ])
    print(table(["GPU", "Ticker", "Index", "Data center", "Marketplace", "Clouds", "24h", "7d", "Page"], rows))
    if args.history == "daily":
        print()
        for item in data.get("indexes") or []:
            daily = item.get("daily") or []
            print(f"{item.get('gpu_name')} daily (newest first, {len(daily)} days)")
            print(table(
                ["Date", "Close", "High", "Low", "Clouds"],
                [[d.get("date"), money(d.get("close")), money(d.get("high")), money(d.get("low")), d.get("clouds")] for d in daily[:14]],
            ))
            print()
    print("Index values are USD per GPU-hour. 24h and 7d are percent changes. Credit " + BASE + ".")


def add_offer_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--gpu")
    parser.add_argument("--vendor")
    parser.add_argument("--provider", help="Cloud id or name, comma-separated")
    parser.add_argument("--cloud-type", choices=["datacenter", "community"])
    parser.add_argument("--pricing", choices=["on_demand", "spot", "any"])
    parser.add_argument("--region")
    parser.add_argument("--min-vram", type=float)
    parser.add_argument("--max-price", type=float)
    parser.add_argument("--in-stock", choices=["true", "false", "any"])
    parser.add_argument("--exclude-resellers", action="store_true")
    parser.add_argument("--sort", choices=["price", "vram"])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--json", action="store_true", help="Print the raw JSON response")


def main() -> None:
    parser = argparse.ArgumentParser(description="Live cloud GPU rental prices from unitedcompute.ai")
    sub = parser.add_subparsers(dest="command", required=True)

    offers = sub.add_parser("offers", help="Search single-GPU offers")
    add_offer_flags(offers)

    gpus = sub.add_parser("gpus", help="One row per GPU model")
    gpus.add_argument("--gpu")
    gpus.add_argument("--vendor")
    gpus.add_argument("--min-vram", type=float)
    gpus.add_argument("--in-stock", choices=["true", "false"])
    gpus.add_argument("--json", action="store_true")

    providers = sub.add_parser("providers", help="Clouds in the index")
    providers.add_argument("--json", action="store_true")

    index = sub.add_parser("index", help="GPU price index")
    index.add_argument("--index", choices=["h100", "h200", "b200", "b300", "a100", "rtx-5090"])
    index.add_argument("--history", choices=["hourly", "daily"])
    index.add_argument("--json", action="store_true")

    args = parser.parse_args()
    {"offers": cmd_offers, "gpus": cmd_gpus, "providers": cmd_providers, "index": cmd_index}[args.command](args)


if __name__ == "__main__":
    main()
