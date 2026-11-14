"""VentoGuard API (FastAPI) + static React frontend, served as one Databricks App."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .lakebase import db, init_ops_schema
from .routers import fleet, genie, turbines, views, work_orders

log = logging.getLogger("ventoguard")
STATIC = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        init_ops_schema()
    except Exception:  # keep serving read-only screens even if the OLTP schema can't be created
        log.exception("Could not initialise vg_ops schema")
    yield


app = FastAPI(title="VentoGuard API", lifespan=lifespan)
for r in (fleet.router, turbines.router, work_orders.router, genie.router, views.router):
    app.include_router(r, prefix="/api")


@app.get("/api/health")
def health():
    return {"ok": True, "lakebase": db.query("SELECT 1 AS ok")[0]["ok"] == 1}


if STATIC.exists():
    app.mount("/assets", StaticFiles(directory=STATIC / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = STATIC / path
        return FileResponse(f if path and f.is_file() else STATIC / "index.html")
