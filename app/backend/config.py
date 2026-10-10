import os

SERVING = os.getenv("SERVING_SCHEMA", "ventoguard_serving")
OPS = os.getenv("OPS_SCHEMA", "vg_ops")
GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID", "")
LAKEBASE_ENDPOINT = os.getenv("LAKEBASE_ENDPOINT", "projects/ventoguard/branches/production/endpoints/primary")
