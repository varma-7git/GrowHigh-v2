import { useCallback, useEffect, useState } from "react";
import WsShell from "../Shell";
import { Stats } from "../kit";
import { Err, all } from "../../admin/ui";
import api, { parseError } from "../../api/client";

const AREA = { JOB_PREP: "Job preparation", CAREER: "Career growth", COMM: "Communication" };
const SEC = { aptitude: "Aptitude", reasoning: "Reasoning", coding: "Coding", technical: "Technical interview", hr: "HR interview", projects: "Projects", technologies: "Technologies", paths: "Career paths", roadmap: "Roadmap",
  spoken: "Spoken English", vocabulary: "Vocabulary", grammar: "Grammar", speaking: "Speaking", listening: "Listening", gd: "Group discussion", presentation: "Presentation", interview: "Interview", professional: "Professional" };
const TYPE = { WRITTEN: "Written", CODE: "Code", UPLOAD: "Upload", URL: "Link", SELECT: "Choice", CHECKLIST: "Checklist", VOICE_TEXT: "Written", RECORDING: "Spoken" };
const waiting = (r) => !r.reviewed_by_name && !r.feedback;
const clock = (t) => `${String(Math.floor(t / 60)).padStart(2, "0")}:${String(t % 60).padStart(2, "0")}`;
const when = (d) => new Date(d).toLocaleString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
const initials = (n) => (n || "?").split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase();

/** One student's answer: a single clear line that opens to the answer and the feedback box. */
function Entry({ x, saved }) {
  const { kind, r } = x;
  const [open, setOpen] = useState(waiting(r));
  const [text, setText] = useState(r.feedback || "");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const type = kind === "rec" ? "Spoken" : r.link ? "Link" : TYPE[r.task_type] || (r.file_url ? "Upload" : "Written");
  const save = async () => {
    if (!text.trim()) { setErr("Write some feedback first."); return; }
    setBusy(true); setErr("");
    try { await api.patch(`${kind === "rec" ? "/recordings" : "/guide-submissions"}/${r.id}/`, { feedback: text.trim() }); saved(); } catch (e) { setErr(parseError(e).message); }
    setBusy(false);
  };
  return (
    <div style={{ borderTop: "1px solid var(--ln, #e6ecf4)" }}>
      <div onClick={() => setOpen(!open)} role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setOpen(!open); } }}
        style={{ display: "flex", alignItems: "center", gap: 14, padding: "14px 4px", cursor: "pointer", flexWrap: "wrap" }}>
        <span aria-hidden="true" style={{ width: 40, height: 40, borderRadius: "50%", background: "var(--n2, #0b2a45)", color: "#fff", display: "grid", placeItems: "center", fontWeight: 700, fontSize: 14, flex: "none" }}>{initials(r.student_name)}</span>
        <span style={{ flex: "1 1 160px", minWidth: 0 }}><b style={{ display: "block" }}>{r.student_name}</b><small style={{ color: "var(--mu, #6b7a90)" }}>{r.login_id} · {when(kind === "rec" ? r.created_at : r.updated_at)}{kind === "rec" ? ` · ${clock(r.seconds)}` : ""}</small></span>
        <span className="ad-pill" style={{ margin: 0 }}>{type}</span>
        <span className={`ad-pill ${waiting(r) ? "warn" : "ok"}`} style={{ margin: 0 }}>{waiting(r) ? "Waiting for feedback" : "Reviewed"}</span>
        <span aria-hidden="true" style={{ color: "var(--mu, #6b7a90)", width: 16, textAlign: "center" }}>{open ? "▾" : "▸"}</span>
      </div>
      {open && (
        <div style={{ padding: "0 4px 20px 54px" }}>
          <div className="ad-eyebrow" style={{ marginBottom: 6 }}>Student's answer</div>
          {kind === "rec" && <audio controls preload="none" src={r.file_url} style={{ width: "100%", margin: "4px 0 12px" }} />}
          {r.choices && r.choices.length > 0 && <p className="ws-p" style={{ margin: "0 0 8px" }}><b>Chose:</b> {r.choices.join(", ")}</p>}
          {r.link && <p className="ws-p" style={{ margin: "0 0 8px" }}><a href={r.link} target="_blank" rel="noreferrer">{r.link} ↗</a></p>}
          {r.text && <div className="ws-p" style={{ whiteSpace: "pre-line", background: "var(--soft, #f4f7fb)", border: "1px solid var(--ln, #e6ecf4)", borderRadius: 12, padding: 14, margin: "0 0 10px", fontFamily: r.task_type === "CODE" ? "ui-monospace, Consolas, monospace" : "inherit" }}>{r.text}</div>}
          {r.file_url && kind !== "rec" && <p className="ws-p" style={{ margin: "0 0 10px" }}><a href={r.file_url} target="_blank" rel="noreferrer">Open the uploaded file ↗</a></p>}
          {!r.text && !r.file_url && !r.link && !(r.choices && r.choices.length) && kind !== "rec" && <p className="ws-p">No written answer was attached.</p>}
          <div className="ad-eyebrow" style={{ margin: "14px 0 6px" }}>Your feedback{r.reviewed_by_name ? ` · by ${r.reviewed_by_name}` : ""}</div>
          <Err e={err} />
          <textarea className="ad-in" rows={3} placeholder={kind === "rec" ? "Pace, clarity, vocabulary, confidence…" : "What was good, and what to improve…"} value={text} onChange={(e) => setText(e.target.value)} />
          <div className="ws-btns"><button className="ad-btn c s" disabled={busy} onClick={save}>{busy ? "Saving…" : r.feedback ? "Update feedback" : "Send feedback"}</button></div>
        </div>)}
    </div>
  );
}

export default function Reviews() {
  const [show, setShow] = useState("pending");
  const [area, setArea] = useState("");
  const [q, setQ] = useState("");
  const [rows, setRows] = useState(null);
  const [subs, setSubs] = useState(null);
  const [guides, setGuides] = useState([]);
  const load = useCallback(() => {
    all("/recordings/").then(setRows).catch(() => setRows([]));
    all("/guide-submissions/").then(setSubs).catch(() => setSubs([]));
    all("/guides/").then(setGuides).catch(() => {});
  }, []);
  useEffect(() => { load(); }, [load]);
  const byId = Object.fromEntries(guides.map((g) => [g.id, g]));
  const byTitle = Object.fromEntries(guides.map((g) => [g.title, g]));
  const place = (r) => byId[r.guide_id] || byTitle[r.guide_title] || null;
  const needle = q.trim().toLowerCase();
  const everything = [...(rows || []).map((r) => ({ kind: "rec", r })), ...(subs || []).map((r) => ({ kind: "sub", r }))];
  const inScope = everything.filter((x) => { const g = place(x.r); return (!area || (g && g.area === area)) && (!needle || `${x.r.student_name} ${x.r.login_id}`.toLowerCase().includes(needle)); });
  const nWait = inScope.filter((x) => waiting(x.r)).length;
  const items = inScope.filter((x) => (show === "pending" ? waiting(x.r) : show === "reviewed" ? !waiting(x.r) : true));
  const tree = {};
  items.forEach((x) => {
    const g = place(x.r);
    const a = g ? g.area : "OTHER", sec = g ? g.section : "other", t = (g && g.title) || x.r.guide_title || "Open answer";
    tree[a] = tree[a] || {}; tree[a][sec] = tree[a][sec] || {}; tree[a][sec][t] = [...(tree[a][sec][t] || []), x];
  });
  const btn = (on) => `ad-btn ${on ? "c" : "o"} s`;
  const ready = rows && subs;
  return (
    <WsShell role="faculty" crumb="Student reviews" title="Student reviews" subtitle="Every spoken answer, written answer and upload from your students, grouped by module and lesson.">
      <Stats items={[["Waiting for feedback", String(everything.filter((x) => waiting(x.r)).length), "Across all lessons"], ["Spoken answers", String((rows || []).length), "Recordings"], ["Written answers and uploads", String((subs || []).length), "Submissions"]]} />
      <div className="ad-card" style={{ marginBottom: 22 }}>
        <div className="ad-eyebrow" style={{ marginBottom: 8 }}>Show</div>
        <div className="ws-btns" style={{ margin: "0 0 16px" }}>
          {[["pending", `Waiting (${nWait})`], ["reviewed", `Reviewed (${inScope.length - nWait})`], ["all", `All (${inScope.length})`]].map(([k, l]) => <button key={k} type="button" className={btn(show === k)} onClick={() => setShow(k)}>{l}</button>)}</div>
        <div className="ad-eyebrow" style={{ marginBottom: 8 }}>Module</div>
        <div className="ws-btns" style={{ margin: "0 0 16px" }}>
          {[["", "All modules"], ...Object.entries(AREA)].map(([k, l]) => <button key={k || "all"} type="button" className={btn(area === k)} onClick={() => setArea(k)}>{l}</button>)}</div>
        <input className="ad-in" style={{ height: 46 }} placeholder="Search by student name or ID" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      {!ready && <div className="ad-empty">Loading…</div>}
      {ready && items.length === 0 && <div className="ad-empty">{everything.length === 0 ? "No student has submitted anything yet." : show === "pending" ? "Nothing is waiting for feedback. Well done." : "Nothing matches these filters."}</div>}
      {Object.entries(tree).map(([a, secs]) => (
        <div key={a} style={{ marginBottom: 34 }}>
          <h2 style={{ margin: "0 0 14px" }}>{AREA[a] || "Other"}<span className="ad-pill">{Object.values(secs).flatMap((l) => Object.values(l)).flat().length}</span></h2>
          {Object.entries(secs).map(([sec, lessons]) => (
            <div key={sec} style={{ marginBottom: 8 }}>
              <div className="ad-eyebrow" style={{ margin: "6px 0 10px" }}>{SEC[sec] || sec}</div>
              {Object.entries(lessons).map(([title, list]) => {
                const w = list.filter((x) => waiting(x.r)).length;
                return (
                  <div key={title} className="ad-card" style={{ marginBottom: 16, padding: "22px 26px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", marginBottom: 6 }}>
                      <h3 style={{ margin: 0, flex: "1 1 200px" }}>{title}</h3>
                      <span className="ad-pill" style={{ margin: 0 }}>{list.length} submission{list.length > 1 ? "s" : ""}</span>
                      <span className={`ad-pill ${w ? "warn" : "ok"}`} style={{ margin: 0 }}>{w ? `${w} waiting` : "All reviewed"}</span>
                    </div>
                    {list.map((x) => <Entry key={`${x.kind}${x.r.id}`} x={x} saved={load} />)}
                  </div>);
              })}
            </div>))}
        </div>))}
    </WsShell>
  );
}
