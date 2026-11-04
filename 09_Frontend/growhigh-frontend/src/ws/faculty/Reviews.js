import { useCallback, useEffect, useState } from "react";
import WsShell from "../Shell";
import { Stats } from "../kit";
import { Err, Select, all } from "../../admin/ui";
import api, { parseError } from "../../api/client";

const clock = (t) => `${String(Math.floor(t / 60)).padStart(2, "0")}:${String(t % 60).padStart(2, "0")}`;

function Item({ r, saved }) {
  const [text, setText] = useState(r.feedback || "");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const save = async () => {
    if (!text.trim()) { setErr("Write some feedback first."); return; }
    setBusy(true); setErr("");
    try { await api.patch(`/recordings/${r.id}/`, { feedback: text.trim() }); saved(); } catch (e) { setErr(parseError(e).message); }
    setBusy(false);
  };
  return (
    <div className="ad-card" style={{ marginBottom: 16 }}>
      <div className="ad-eyebrow">{r.reviewed_by_name ? `Reviewed by ${r.reviewed_by_name}` : "Waiting for feedback"}</div>
      <h2 style={{ margin: "8px 0 4px" }}>{r.student_name} <small style={{ color: "var(--mu)", fontWeight: 600 }}>{r.login_id}</small></h2>
      <div className="ws-p">{r.guide_title || "Open answer"} · {new Date(r.created_at).toLocaleString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })} · {clock(r.seconds)}</div>
      <audio controls preload="none" src={r.file_url} style={{ width: "100%", margin: "12px 0" }} />
      <Err e={err} />
      <textarea className="ad-in" rows={3} placeholder="Pace, clarity, vocabulary, confidence…" value={text} onChange={(e) => setText(e.target.value)} />
      <div className="ws-btns"><button className="ad-btn c s" disabled={busy} onClick={save}>{busy ? "Saving…" : r.feedback ? "Update feedback" : "Send feedback"}</button></div>
    </div>
  );
}

export default function Reviews() {
  const [show, setShow] = useState("pending");
  const [rows, setRows] = useState(null);
  const load = useCallback(() => { all("/recordings/", show === "pending" ? { pending: 1 } : {}).then(setRows).catch(() => setRows([])); }, [show]);
  useEffect(() => { setRows(null); load(); }, [load]);
  return (
    <WsShell role="faculty" crumb="Speaking reviews" title="Speaking reviews" subtitle="Listen to your students' spoken answers and give feedback.">
      <Stats items={[["Showing", String((rows || []).length), show === "pending" ? "Waiting for feedback" : "All recordings"]]} />
      <div className="ad-filters"><Select value={show} onChange={setShow} options={[["pending", "Waiting for feedback"], ["all", "All recordings"]]} /></div>
      {rows && rows.length === 0 && <div className="ad-empty">{show === "pending" ? "Nothing is waiting. New recordings appear here." : "No student has recorded an answer yet."}</div>}
      {(rows || []).map((r) => <Item key={r.id} r={r} saved={load} />)}
    </WsShell>
  );
}
