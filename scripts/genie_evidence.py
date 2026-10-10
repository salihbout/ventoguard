"""Ask the VentoGuard Genie space real questions via the Conversation API and log question -> SQL -> result as Markdown.

Usage: python scripts/genie_evidence.py <profile> <space_id> <out.md>
Uses the same SDK calls as app/app.py (start_conversation_and_wait / get_message_attachment_query_result).
"""
import sys
from datetime import datetime, timezone

from databricks.sdk import WorkspaceClient

QUESTIONS = [
    "Which wind farm lost the most revenue to unplanned failures, and which component caused it?",
    "Show the 10 turbines with the highest failure probability and their likely component",
    "What was technical availability per farm by month?",
    "How much money is at stake on turbines currently at risk?",
    "Which technician notes mention failure precursors in the last 30 days?",
    "Do Hansa Drives gearboxes fail more often than NordGear ones?",
]


def md_table(cols, rows, limit=15):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join("" if v is None else str(v).replace("|", "/").replace("\n", " ") for v in r) + " |" for r in rows[:limit]]
    if len(rows) > limit:
        out.append(f"\n_… {len(rows) - limit} more rows_")
    return "\n".join(out)


def main(profile, space_id, out_path):
    w = WorkspaceClient(profile=profile)
    lines = [f"# Genie space conversations: execution evidence", "",
             f"Space `{space_id}` (*VentoGuard Reliability: Wind Fleet Analytics*), asked via the Genie Conversation API on "
             f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}. Everything below is returned verbatim by Genie (answer text, generated SQL, result rows).", ""]
    for q in QUESTIONS:
        msg = w.genie.start_conversation_and_wait(space_id, q)
        lines += [f"## Q: {q}", "", f"_status: {msg.status.value if msg.status else '?'} · conversation {msg.conversation_id}_", ""]
        for a in msg.attachments or []:
            if a.text and a.text.content:
                lines += ["**Genie:** " + a.text.content.strip(), ""]
            if a.query:
                if a.query.description:
                    lines += ["**Genie:** " + a.query.description.strip(), ""]
                lines += ["```sql", a.query.query.strip(), "```"]
                res = w.genie.get_message_attachment_query_result(space_id, msg.conversation_id, msg.message_id, a.attachment_id)
                sr = res.statement_response
                if sr and sr.result and sr.result.data_array is not None:
                    lines += ["", md_table([c.name for c in sr.manifest.schema.columns], sr.result.data_array), ""]
        lines.append("")
        print("answered:", q)
    open(out_path, "w").write("\n".join(lines))


if __name__ == "__main__":
    main(*sys.argv[1:])
