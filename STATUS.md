# VentoGuard: status and handoff

_Last updated 2026-10-15. Workspace `fevm-serverless-stable-7zqte5`, CLI profile `demo`._

## Done
- **Build complete and running.** All six stages: Lakeflow → Unity Catalog → ML + GenAI → Lakebase → Genie → Databricks App.
- **Layout:** default catalog `serverless_stable_7zqte5_catalog`, schemas `ventoguard_bronze` (+ Volume `raw_landing`), `ventoguard_silver`, `ventoguard_gold`, `ventoguard_serving`.
- **Bundle target `demo`** (the default): job `[demo salih_boutadghart] ventoguard-end-to-end` (id `840197049618132`), pipeline `7960386e-d964-4067-a736-b4871849e2c4`.
  The last full run, `103975912547790`, had all 6 tasks succeed on the first attempt.
- **Genie space** `01f1c4d953cb132e838ecd828813a354`. **Lakebase** project `ventoguard`, synced tables in `ventoguard_serving`; the app writes work orders to `vg_ops.work_orders`.
- **App** `ventoguard`: https://ventoguard-7474660468503815.aws.databricksapps.com. React + Du Bois source in `app_ui/`, built into `app/static`; FastAPI in `app/backend`.
  The UI was browser-tested locally; the deployed app was verified through its API (see `evidence/app.md`).
- **Evidence** (all text) in `evidence/`. **Deck** in `deck/VentoGuard_deck.pdf` and `.md`; its numbers come from `deck/extract_numbers.py`.
- Git: committed locally on `main`, **not pushed**.

## Pending
1. **Push to GitHub**, so the validator can read the repo. Either a public repo (e.g. `salihbout` account) or a private repo on the EMU account with GitHub connected in the submission form.
2. **Submit the form**: repo link, deck PDF, optional conversation ID.
3. **Decide on the legacy v1 deployment** (unused, not deleted). It consists of the `wind_reliability` schema, the `vg_serving` synced tables,
   the old bundle target `dev` job/pipeline (job `1081515418325428`, pipeline `6c84e3c6-18a3-4951-a75d-32be1e8d21f2`) and Genie space `01f1c4c082b419f88ccebeab3614bc27`.
   Removing the pipeline also drops its tables.
4. **Optional:** browser-test the deployed app (it needs an Okta push approval), and run the design audit (`databricks-impeccable:audit`) on `app_ui/`.

## Resume / re-run
```bash
databricks bundle deploy -t demo --profile demo
databricks bundle run ventoguard_end_to_end -t demo --profile demo
# then regenerate evidence + deck (see README "Reproduce")
cd app_ui && npm install && npm run build      # → app/static; npm needs .npmrc legacy-peer-deps + overrides (proxy quarantine)
```

## Gotchas
- Governed tag policies exist on `domain`, `medallion_layer`, `pii`, `use_case`, `owner_team`, `business_unit` and `certified`. Use only their allowed values.
- No CREATE CATALOG permission, so synced tables live in a standard-catalog schema.
- In serverless notebooks, `psycopg[binary]` can SIGABRT on import, so use `pg8000`.
- Locally, pip and npm proxies block recently released versions. Pin to older releases in the same major.
- When running the API locally, use `OPS_SCHEMA=vg_ops_dev`, so that the app's service principal keeps ownership of `vg_ops`.
