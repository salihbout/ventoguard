"""Export executed Databricks notebook task runs (code + outputs) to readable Markdown.

Usage: python scripts/export_run_evidence.py <profile> <out_dir> <name>=<task_run_id> [<name>=<task_run_id> ...]

`databricks jobs export-run` returns the rendered notebook as HTML, with the notebook model (every command and its
results) embedded as base64 + URL-encoded JSON. This script decodes that model and writes each cell's source
and its text/table output as Markdown, so the execution evidence can be read as plain text in the repo.
"""
import base64
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path


def export(profile: str, run_id: str) -> dict:
    out = subprocess.run(["databricks", "jobs", "export-run", run_id, "--views-to-export", "CODE", "--profile", profile, "-o", "json"],
                         check=True, capture_output=True, text=True).stdout
    html = json.loads(out)["views"][0]["content"]
    m = re.search(r"__DATABRICKS_NOTEBOOK_MODEL = '([^']+)'", html)
    return json.loads(urllib.parse.unquote(base64.b64decode(m.group(1)).decode("utf-8")))


def table_md(data, schema, max_rows=40) -> str:
    cols = [c["name"] for c in schema]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in data[:max_rows]:
        cells = [str(v).replace("|", "\\|").replace("\n", " ") if v is not None else "null" for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    if len(data) > max_rows:
        lines.append(f"\n_… {len(data) - max_rows} more rows_")
    return "\n".join(lines)


def to_markdown(model: dict, run_id: str) -> str:
    md = [f"# {model.get('name')}: executed notebook (task run {run_id})", "",
          "> Exported from the Databricks job run with `databricks jobs export-run`; cell sources and their outputs "
          "exactly as executed on serverless compute.", ""]
    for i, cmd in enumerate(sorted(model.get("commands", []), key=lambda c: c.get("position", 0)), 1):
        src = cmd.get("command", "")
        if src.lstrip().startswith("%md"):
            md += [re.sub(r"^%md ?", "", src.lstrip()), ""]
            continue
        lang = "sql" if src.lstrip().startswith("%sql") else "python"
        md += [f"### Cell {i}", f"```{lang}", src.strip(), "```"]
        res = cmd.get("results") or {}
        rtype, data = res.get("type"), res.get("data")
        if rtype == "table" and data is not None:
            md += ["**Output:**", "", table_md(data, res.get("schema", []))]
        elif rtype in ("text", "html") or isinstance(data, str):
            text = data if isinstance(data, str) else json.dumps(data)
            text = re.sub(r"<[^>]+>", "", text) if rtype == "html" else text
            if text.strip():
                md += ["**Output:**", "```text", text.strip()[:6000], "```"]
        elif rtype == "listResults":
            for sub in data or []:
                if sub.get("type") == "table":
                    md += ["**Output:**", "", table_md(sub.get("data", []), sub.get("schema", []))]
                elif isinstance(sub.get("data"), str) and sub["data"].strip():
                    md += ["**Output:**", "```text", sub["data"].strip()[:6000], "```"]
        if cmd.get("error") or res.get("cause"):
            md += ["**Error:**", "```text", str(cmd.get("error") or res.get("cause"))[:3000], "```"]
        md.append("")
    return "\n".join(md)


if __name__ == "__main__":
    profile, out_dir, *run_ids = sys.argv[1:]
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for arg in run_ids:
        name, rid = arg.split("=")
        model = export(profile, rid)
        path = Path(out_dir) / f"{name}.md"
        path.write_text(to_markdown(model, rid))
        print("wrote", path)
