# Changelog

Format changes to the dataset and the API. Adding a column is not breaking; renaming or removing
one bumps `schema_version` (in `data/schema.json` and `offers.json`).

## Schema version 1 (25 Nov 2026)

Breaking: column names now match the live API (unitedcompute.ai/api/v1), defined once in
`data/schema.json`. History files were rewritten once in the new format.

| Old | New |
|---|---|
| `cloud`, `cloud_name` | `provider_id`, `provider_name` |
| `gpu` | `gpu_id` |
| `tier` (`secure` / `community`) | `cloud_type` (`datacenter` / `community`) |
| `list_price`, `price_now` | `list_price_per_hour`, `price_per_hour` |
| `stock` | `stock_level` |
| `last_checked_at`, `last_changed_at` | `checked_at`, `changed_at` |
| `regions` `{"US":"low"}` | `[{"id":"US","location":"United States","stock":"low"}]` |
| `clouds.csv` `cloud` | `id` |
| `gpus.csv` `gpu` | `id` |

New: `offer_id` (several products of one cloud can map to the same GPU), `currency`, `gpu_count`,
`provider_url`, `fresh` (offers not checked for 2 hours have no current price, as in the API),
Parquet files for every table, `daily_prices`, `index_daily`, `price_changes.parquet`,
`SCHEMA.md`. Booleans are `true`/`false`.
