from fastapi import APIRouter, HTTPException

from ..config import GENIE_SPACE_ID
from ..lakebase import ws
from ..models import GenieAnswer, GenieAsk

router = APIRouter(tags=["genie"])
MAX_ROWS = 200


@router.post("/genie/ask", response_model=GenieAnswer)
def ask(body: GenieAsk):
    if not GENIE_SPACE_ID:
        raise HTTPException(503, "Genie space is not configured")
    w = ws()
    msg = (w.genie.create_message_and_wait(GENIE_SPACE_ID, body.conversation_id, body.question) if body.conversation_id
           else w.genie.start_conversation_and_wait(GENIE_SPACE_ID, body.question))
    out = GenieAnswer(conversation_id=msg.conversation_id, message_id=msg.message_id,
                      status=msg.status.value if msg.status else "UNKNOWN", text="")
    texts = []
    for a in msg.attachments or []:
        if a.text and a.text.content:
            texts.append(a.text.content.strip())
        if a.query:
            if a.query.description:
                texts.append(a.query.description.strip())
            out.sql = a.query.query
            res = w.genie.get_message_attachment_query_result(GENIE_SPACE_ID, msg.conversation_id, msg.message_id, a.attachment_id)
            sr = res.statement_response
            if sr and sr.manifest and sr.manifest.schema:
                out.columns = [c.name for c in sr.manifest.schema.columns]
            if sr and sr.result and sr.result.data_array:
                out.rows = sr.result.data_array[:MAX_ROWS]
                out.row_count = len(sr.result.data_array)
    out.text = "\n\n".join(texts)
    return out
