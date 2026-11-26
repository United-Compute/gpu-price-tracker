// United Compute GPU Prices: Apify Actor.
// A thin client for the free public API at https://unitedcompute.ai/api. One run = one API call;
// every row is pushed to the default dataset. No scraping, no proxy, no API key.
import { Actor, log } from "apify";

const BASE = "https://unitedcompute.ai";
const UA = "uc-apify/1.0 (+https://apify.com)";

await Actor.init();
const input = (await Actor.getInput()) ?? {};
const mode = input.mode ?? "offers";

const q = new URLSearchParams();
const set = (k, v) => { if (v !== undefined && v !== null && v !== "") q.set(k, String(v)); };

let path, list;
if (mode === "offers") {
  path = "/api/v1/offers";
  list = "offers";
  set("gpu", input.gpu);
  set("provider", input.provider);
  set("region", input.region);
  set("cloud_type", input.cloudType === "any" ? undefined : input.cloudType);
  set("pricing", input.pricing);
  set("in_stock", input.inStock);
  set("min_vram", input.minVram);
  set("max_price", input.maxPrice);
  set("vendor", input.vendor === "any" ? undefined : input.vendor);
  if (input.excludeResellers) set("exclude_resellers", "true");
  set("sort", input.sort);
  set("limit", input.limit ?? 100);
} else if (mode === "gpus") {
  path = "/api/v1/gpus";
  list = "gpus";
  set("gpu", input.gpu);
  set("vendor", input.vendor === "any" ? undefined : input.vendor);
  set("min_vram", input.minVram);
  if (input.inStock === "true") set("in_stock", "true");
} else if (mode === "providers") {
  path = "/api/v1/providers";
  list = "providers";
} else if (mode === "index") {
  path = "/api/v1/index";
  list = "indexes";
  set("index", input.index);
  set("history", input.history === "none" ? undefined : input.history);
} else {
  throw new Error(`Unknown mode "${mode}". Use offers, gpus, providers or index.`);
}

const url = `${BASE}${path}${q.size ? `?${q}` : ""}`;
log.info(`GET ${url}`);
const res = await fetch(url, { headers: { "user-agent": UA, accept: "application/json" } });
if (!res.ok) throw new Error(`API returned ${res.status}: ${(await res.text()).slice(0, 300)}`);
const body = await res.json();
const rows = body[list] ?? [];

// The index endpoint returns one object per index with a nested history: flatten it into one row
// per point, which is what people chart.
let items = rows;
if (mode === "index" && input.history && input.history !== "none") {
  items = rows.flatMap((ix) => {
    const points = ix[input.history] ?? [];
    return points.map((p) => ({ index: ix.index, ticker: ix.ticker, gpu_id: ix.gpu_id, gpu_name: ix.gpu_name, ...p }));
  });
}

await Actor.pushData(items.map((r) => ({ ...r, source: "United Compute (unitedcompute.ai), CC BY 4.0", api_updated_at: body.updated_at ?? null })));
await Actor.setValue("OUTPUT", { url, count: items.length, updated_at: body.updated_at ?? null, stale: body.stale ?? null });
log.info(`Saved ${items.length} rows. Data checked ${body.updated_at ?? "n/a"}${body.stale ? " (stale: last check over an hour old)" : ""}.`);
await Actor.exit();
