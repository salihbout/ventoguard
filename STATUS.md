# VentoGuard: status and handoff

_Last updated 2026-11-14. Workspace `fevm-serverless-stable-7zqte5`, CLI profile `demo`._

## Done
- **Build complete and running.** All six stages: Lakeflow → Unity Catalog → ML + GenAI → Lakebase → Genie → Databricks App.
- **Layout:** default catalog `serverless_stable_7zqte5_catalog`, schemas `ventoguard_bronze` (+ Volume `raw_landing`), `ventoguard_silver`, `ventoguard_gold`, `ventoguard_serving`.
- **Bundle target `demo`** (the default): job `[demo salih_boutadghart] ventoguard-end-to-end` (id `840197049618132`), pipeline `7960386e-d964-4067-a736-b4871849e2c4`.
  The last full run, `103975912547790`, had all 6 tasks succeed on the first attempt.
- **Genie space** `01f1c4d953cb132e838ecd828813a354`. **Lakebase** project `ventoguard`, synced tables in `ventoguard_serving`; the app writes work orders to `vg_ops.work_orders`.
- **App** `ventoguard`: https://ventoguard-7474660468503815.aws.databricksapps.com. React + Du Bois source in `app_ui/`, built into `app/static`; FastAPI in `app/backend`.
  The UI was browser-tested locally; the deployed app was verified through its API (see `evidence/app.md`).
- **Evidence** (all text) in `evidence/`. **Deck** in `deck/VentoGuard_deck.pdf` and `.md` (14 slides for Aerion Windkraft AG, a fictional customer; the HTML is an arrow-key presentation, rebuilt 2026-11-14 for the AI role-play); its numbers come from `deck/extract_numbers.py`. The role-play talk track and Q&A are in `deck/ROLEPLAY_PLAYBOOK.md`.
- Git: pushed to the public repo https://github.com/salihbout/ventoguard (`main`, remote `personal`), which is the one to submit. It is mirrored to the private EMU repo https://github.com/salih-boutadghart_data/ventoguard (remote `origin`).

## Pending
1. **Submit the form**: repo link https://github.com/salihbout/ventoguard (public, so the validator can read it without connecting GitHub), deck PDF, optional conversation ID.
2. **Legacy v1 deployment is kept on purpose** (decided 2026-10-17). It consists of the `wind_reliability` schema, the `vg_serving` synced tables,
   the old bundle target `dev` job/pipeline (job `1081515418325428`, pipeline `6c84e3c6-18a3-4951-a75d-32be1e8d21f2`) and Genie space `01f1c4c082b419f88ccebeab3614bc27`.
   Removing the pipeline also drops its tables.
3. **Before the role-play:** run the pre-demo checklist in `deck/ROLEPLAY_PLAYBOOK.md`. On 2026-11-14 the app's compute was found stopped (since 2026-11-06). It was restarted and redeployed. The latest deployment is `01f1e0606d771120b73951b6764d8056` (2026-11-14: role views for the COO, asset management and operations; Aerion logo; interactive map), RUNNING. A 4th synced table `gold_failure_history` was added (SELECT granted to the app service principal; the refresh job re-grants after each sync), and duplicate test work order #1 was deleted (one F01-T20 order remains). If the app has stopped again on the day, run `databricks apps start ventoguard --profile demo`, then `databricks apps deploy ventoguard --source-code-path /Workspace/Users/salih.boutadghart@databricks.com/ventoguard_app --profile demo`.
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
