import { Button } from "@databricks/design-system";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { ErrorState, Loading } from "../components/States";
import { api, type GenieAnswer } from "../lib/api";

const SUGGESTIONS = [
  "Which wind farm lost the most revenue to unplanned failures, and which component caused it?",
  "Show the 10 turbines with the highest failure probability and their likely component",
  "What was technical availability per farm by month?",
  "Do Hansa Drives gearboxes fail more often than NordGear ones?",
];

interface Turn { q: string; a?: GenieAnswer; error?: unknown }

function ResultTable({ a }: { a: GenieAnswer }) {
  if (!a.columns.length) return null;
  return (
    <div className="table-scroll" style={{ maxHeight: 360 }}>
      <table className="table">
        <thead><tr>{a.columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>{a.rows.map((r, i) => <tr key={i}>{r.map((v, j) => <td key={j} className={v !== null && !isNaN(Number(v)) ? "num" : ""}>{v ?? "–"}</td>)}</tr>)}</tbody>
      </table>
      {a.row_count > a.rows.length && <p className="small muted">Showing {a.rows.length} of {a.row_count} rows.</p>}
    </div>
  );
}

export function AskPage() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const conversationId = [...turns].reverse().find((t) => t.a)?.a?.conversation_id;
  const ask = useMutation({
    mutationFn: (q: string) => api.askGenie(q, conversationId),
    onMutate: (q) => setTurns((t) => [...t, { q }]),
    onSuccess: (a) => setTurns((t) => t.map((x, i) => (i === t.length - 1 ? { ...x, a } : x))),
    onError: (error) => setTurns((t) => t.map((x, i) => (i === t.length - 1 ? { ...x, error } : x))),
  });
  const submit = (q: string) => { if (q.trim().length >= 3 && !ask.isPending) { ask.mutate(q.trim()); setInput(""); } };

  return (
    <main className="page" style={{ maxWidth: 1100 }}>
      <header className="page-head">
        <h1>Ask the fleet</h1>
        <p>Plain-language questions about failures, losses, availability, risk and technician notes. Answers come from the
           <strong> VentoGuard Reliability</strong> Genie space over governed Unity Catalog tables. Every answer shows the SQL it ran.</p>
      </header>

      {turns.length === 0 && (
        <section aria-label="Suggested questions" className="suggestions">
          {SUGGESTIONS.map((s) => <Button componentId="vg.genie.suggest" key={s} onClick={() => submit(s)}>{s}</Button>)}
        </section>
      )}

      <div className="chat" aria-live="polite">
        {turns.map((t, i) => (
          <article key={i} className="panel turn-a">
            <div className="turn-q">{t.q}</div>
            {!t.a && !t.error && <Loading label="Genie is writing and running the query" />}
            {t.error !== undefined && <ErrorState error={t.error} />}
            {t.a && (
              <>
                {t.a.text && <div className="answer">{t.a.text.replace(/\*\*/g, "")}</div>}
                <ResultTable a={t.a} />
                {t.a.sql && (
                  <details>
                    <summary className="small" style={{ cursor: "pointer", minHeight: 32 }}>Generated SQL</summary>
                    <pre className="sql">{t.a.sql}</pre>
                  </details>
                )}
                <div className="provenance">Answered by Genie · space VentoGuard Reliability · status {t.a.status.toLowerCase()}</div>
              </>
            )}
          </article>
        ))}
      </div>

      <form className="ask-bar" onSubmit={(e) => { e.preventDefault(); submit(input); }}>
        <input aria-label="Question for Genie" placeholder={turns.length ? "Ask a follow-up" : "Ask a question about the fleet"}
               value={input} onChange={(e) => setInput(e.target.value)} maxLength={1000} />
        <Button componentId="vg.genie.ask" type="primary" htmlType="submit" loading={ask.isPending} disabled={input.trim().length < 3}>Ask</Button>
      </form>
      {turns.length > 0 && (
        <div><Button componentId="vg.genie.reset" type="tertiary" onClick={() => setTurns([])}>Start a new conversation</Button></div>
      )}
    </main>
  );
}
