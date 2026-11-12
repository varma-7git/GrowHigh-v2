import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import WsShell from "../Shell";
import { Btn, Stats, Tabs } from "../kit";
import { Ic } from "../icons";
import { Modal, all } from "../../admin/ui";
import api, { parseError } from "../../api/client";
import Recorder from "./Recorder";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

const KIND = { NOTES: "Notes", VIDEO: "Video", PDF: "PDF", LINK: "Web link", AUDIO: "Audio" };
const SUBJECT_AREA = { aptitude: "APTITUDE", reasoning: "REASONING", coding: "CODING", technical: "TECHNICAL", hr: "HR" };

const LETTER = ["A", "B", "C", "D"];

/** Practice questions on a lesson: one at a time with Previous/Next, optional timer, then score, accuracy and explanations. */
function QuizDialog({ g, onClose, onPassed }) {
  const [qs, setQs] = useState(null);
  const [ans, setAns] = useState({});
  const [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [stage, setStage] = useState("start");
  const [idx, setIdx] = useState(0);
  const [timed, setTimed] = useState(false);
  const [shuffle, setShuffle] = useState(g.section === "reasoning");
  const [left, setLeft] = useState(0);
  const [began, setBegan] = useState(0);
  useEffect(() => { api.get(`/guides/${g.id}/quiz/`).then((r) => setQs(r.data.questions)).catch((e) => setErr(parseError(e).message)); }, [g.id]);
  const begin = () => {
    let list = [...qs];
    if (shuffle) list = list.sort(() => Math.random() - 0.5);
    setQs(list); setAns({}); setIdx(0); setRes(null); setLeft(list.length * 60); setBegan(Date.now()); setStage("run");
  };
  const submit = useCallback(async () => {
    setBusy(true); setErr("");
    try {
      const { data } = await api.post(`/guides/${g.id}/quiz/`, { answers: ans, timed, seconds: Math.round((Date.now() - began) / 1000) });
      setRes(data); setStage("result"); onPassed();
    } catch (e) { setErr(parseError(e).message); }
    setBusy(false);
  }, [g.id, ans, timed, began, onPassed]);
  useEffect(() => {
    if (stage !== "run" || !timed) return undefined;
    if (left <= 0) { submit(); return undefined; }
    const t = setTimeout(() => setLeft((x) => x - 1), 1000);
    return () => clearTimeout(t);
  }, [stage, timed, left, submit]);
  const answered = (q) => ans[q.id] !== undefined && ans[q.id] !== "";
  const q = qs && qs[idx];
  const mm = (n) => `${Math.floor(n / 60)}:${String(n % 60).padStart(2, "0")}`;
  return (
    <Modal title={`Practice: ${g.title}`} onClose={onClose}>
      {err && <div className="ad-alert danger" role="alert">{err}</div>}
      {!qs && !err && <p className="ws-p">Loading…</p>}
      {qs && stage === "start" && (<>
        <p className="ws-p">{qs.length} question{qs.length > 1 ? "s" : ""}. Score 40% or more to pass. Answers and explanations appear after you submit.</p>
        <label style={{ display: "flex", gap: 10, alignItems: "center", padding: "6px 0" }}><input type="checkbox" checked={timed} onChange={(e) => setTimed(e.target.checked)} /> Timed test (1 minute per question)</label>
        <label style={{ display: "flex", gap: 10, alignItems: "center", padding: "6px 0" }}><input type="checkbox" checked={shuffle} onChange={(e) => setShuffle(e.target.checked)} /> Shuffle the questions</label>
        <div className="ad-act" style={{ justifyContent: "flex-start" }}>
          <button className="ad-btn p" onClick={begin}>Start</button><button type="button" className="ad-btn o" onClick={onClose}>Cancel</button></div>
      </>)}
      {qs && stage === "run" && q && (<>
        <div className="ws-p" style={{ display: "flex", justifyContent: "space-between" }}>
          <span>Question {idx + 1} of {qs.length} · {qs.filter(answered).length} answered</span>{timed && <b>{mm(left)}</b>}</div>
        <progress value={qs.filter(answered).length} max={qs.length} style={{ width: "100%" }} />
        <h3 style={{ margin: "14px 0 10px" }}>{q.text}</h3>
        {q.qtype === "NUMERIC" ? (
          <input className="ad-in" inputMode="decimal" placeholder="Type your answer as a number" value={ans[q.id] ?? ""} onChange={(e) => setAns({ ...ans, [q.id]: e.target.value })} />
        ) : q.options.map((o, k) => (
          <label key={k} style={{ display: "flex", gap: 10, alignItems: "center", padding: "8px 0", cursor: "pointer" }}>
            <input type="radio" name={`q${q.id}`} checked={ans[q.id] === k} onChange={() => setAns({ ...ans, [q.id]: k })} /> <span>{LETTER[k]}. {o}</span>
          </label>))}
        <div className="ws-btns" style={{ margin: "14px 0" }}>
          {qs.map((x, i) => <button key={x.id} type="button" className={`ad-btn ${i === idx ? "p" : answered(x) ? "c" : "o"} s`} onClick={() => setIdx(i)}>{i + 1}</button>)}</div>
        <div className="ad-act" style={{ justifyContent: "flex-start" }}>
          <button type="button" className="ad-btn o" disabled={idx === 0} onClick={() => setIdx(idx - 1)}>Previous</button>
          {idx < qs.length - 1 && <button type="button" className="ad-btn o" onClick={() => setIdx(idx + 1)}>Next</button>}
          <button className="ad-btn p" disabled={busy || qs.filter(answered).length === 0} onClick={submit}>{busy ? "Checking…" : "Submit answers"}</button></div>
        {qs.filter(answered).length < qs.length && <p className="ws-p" style={{ fontSize: 13 }}>{qs.length - qs.filter(answered).length} unanswered question{qs.length - qs.filter(answered).length > 1 ? "s" : ""} will count as wrong.</p>}
      </>)}
      {res && stage === "result" && (<>
        <div className={`ad-alert ${res.passed ? "success" : "danger"}`} role="status">
          You scored {res.score} out of {res.total}. Accuracy {res.accuracy}%{res.seconds ? ` · Time ${mm(res.seconds)}` : ""}. {res.passed ? (res.lesson_completed ? "Lesson completed." : "Practice passed. Now do the hands-on task to complete the lesson.") : "You need 40% to pass. Read the lesson again and retry."}</div>
        {res.review.map((r, i) => (
          <div key={r.id} style={{ marginBottom: 14 }}>
            <b>{i + 1}. {r.text}</b>
            <div className="ws-p">Your answer: {r.selected === null ? "—" : r.qtype === "NUMERIC" ? String(r.selected) : `${LETTER[r.selected]}. ${r.options[r.selected]}`} {r.is_correct ? "✓" : `✗ · Correct: ${r.correct_text}`}</div>
            {r.explanation && <small>{r.explanation}</small>}
          </div>))}
        <div className="ad-act" style={{ justifyContent: "flex-start" }}>
          <button className="ad-btn p" onClick={() => setStage("start")}>{res.passed ? "Practise again" : "Try again"}</button>
          <button type="button" className="ad-btn o" onClick={onClose}>Close</button></div>
      </>)}
    </Modal>
  );
}

/** The task for one lesson: questions, a recording, a written answer or an upload. Doing it completes the lesson. */
function TaskBox({ g, task, reload }) {
  const [quiz, setQuiz] = useState(false);
  const sub = task.submission;
  const [text, setText] = useState(sub ? sub.text : "");
  const [file, setFile] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [picked, setPicked] = useState(sub && sub.choices ? sub.choices : []);
  const [link, setLink] = useState(sub && sub.link ? sub.link : "");
  const opts = task.options || [];
  const toggle = (o) => setPicked(picked.includes(o) ? picked.filter((x) => x !== o) : [...picked, o]);
  const send = async (e) => {
    e.preventDefault(); setErr("");
    const t = task.type;
    if ((t === "WRITTEN" || t === "VOICE_TEXT") && text.trim().length < 20) return setErr("Write at least 20 characters.");
    if (t === "CODE" && text.trim().length < 15) return setErr("Paste or write your code (at least 15 characters).");
    if (t === "SELECT" && !picked.length) return setErr("Choose at least one item from the list.");
    if (t === "SELECT" && text.trim().length < 10) return setErr("Explain your choice in at least 10 characters.");
    if (t === "CHECKLIST" && picked.length !== opts.length) return setErr("Tick every item on the checklist.");
    if (t === "URL" && !/^https?:\/\/\S+\.\S+/i.test(link.trim())) return setErr("Enter a full link starting with http:// or https://");
    if (t === "UPLOAD" && !file) return setErr("Choose a file to upload.");
    setBusy(true);
    const fd = new FormData();
    fd.append("text", text);
    if (t === "URL") fd.append("link", link.trim());
    if (t === "SELECT" || t === "CHECKLIST") picked.forEach((c) => fd.append("choices", c));
    if (file) fd.append("file", file);
    try { await api.post(`/guides/${g.id}/submit/`, fd); setFile(null); reload(); }
    catch (x) { const p = parseError(x); setErr(Object.values(p.fields || {}).flat().join(" ") || p.message); }
    setBusy(false);
  };
  // Hands-on answers must be typed by the student: copying, cutting, pasting, dropping text and the right-click menu are blocked
  const noCopy = { onPaste: (e) => e.preventDefault(), onCopy: (e) => e.preventDefault(), onCut: (e) => e.preventDefault(), onDrop: (e) => e.preventDefault(), onContextMenu: (e) => e.preventDefault(), autoComplete: "off", spellCheck: false };
  const hasQ = task.questions > 0;
  const taskDone = task.type === "RECORDING" ? g.done : task.type === "VOICE_TEXT" ? g.done : !!sub;
  const Tick = ({ ok }) => <span style={{ color: ok ? "var(--tint-green-fg, #14703d)" : "var(--mu2, #56667f)", fontWeight: 700 }}>{ok ? "✓ Done" : "To do"}</span>;
  return (
    <div style={{ borderTop: "1px solid var(--ln, #e3e9f1)", marginTop: 14, paddingTop: 14 }}>
      <p className="ws-p" style={{ fontSize: 13, color: "var(--mu2, #56667f)", margin: "0 0 10px" }}>{hasQ ? "Do both parts to complete this lesson: practise the questions, then do the hands-on task." : "Do the hands-on task to complete this lesson."}</p>
      {hasQ && (
        <div style={{ marginBottom: 16 }}>
          <div className="ad-eyebrow">Practice questions · <Tick ok={task.quiz_passed} /></div>
          <p className="ws-p">{task.questions} question{task.questions > 1 ? "s" : ""} on this topic. Score 40% or more.{task.quiz_best !== null ? ` Your best: ${task.quiz_best}%.` : ""}</p>
          <div className="ws-btns"><button className="ad-btn c s" onClick={() => setQuiz(true)}>{task.quiz_best !== null ? "Practise again" : "Start practice"}</button></div>
          {quiz && <QuizDialog g={g} onClose={() => setQuiz(false)} onPassed={reload} onDone={reload} />}
        </div>)}
      <div className="ad-eyebrow">Hands-on task · <Tick ok={taskDone} /></div>
      {(task.type === "RECORDING" || task.type === "VOICE_TEXT") && (<><p className="ws-p">{task.prompt}</p><Recorder guide={g} onSaved={reload} /></>)}
      {task.type !== "RECORDING" && (
        <form onSubmit={send} noValidate style={task.type === "VOICE_TEXT" ? { marginTop: 14 } : null}>
          {task.type !== "VOICE_TEXT" && <p className="ws-p">{task.prompt}</p>}
          {["WRITTEN", "CODE", "SELECT", "VOICE_TEXT"].includes(task.type) && <p className="ws-p" style={{ fontSize: 13, color: "var(--mu2, #56667f)" }}>Type your answer yourself. Copy and paste are turned off for hands-on tasks.</p>}
          {task.type === "VOICE_TEXT" && <p className="ws-p"><b>Then write your answer</b> (the lesson completes when you have recorded and written).</p>}
          {(task.type === "SELECT" || task.type === "CHECKLIST") && (
            <div style={{ display: "grid", gap: 8, margin: "8px 0" }}>
              {opts.map((o) => (
                <label key={o} style={{ display: "flex", gap: 10, alignItems: "center", padding: "10px 12px", border: "1px solid var(--ln, #e3e9f1)", borderRadius: 12, cursor: "pointer", background: picked.includes(o) ? "var(--sel, #eaf3ff)" : "#fff" }}>
                  <input type="checkbox" checked={picked.includes(o)} onChange={() => toggle(o)} /> {o}</label>))}
              <span className="ws-p" style={{ fontSize: 13 }}>{task.type === "CHECKLIST" ? `${picked.length} of ${opts.length} done` : `${picked.length} selected`}</span>
            </div>)}
          {task.type === "URL" && <input className="ad-in" type="url" placeholder="https://github.com/your-name/your-project" value={link} onChange={(e) => setLink(e.target.value)} />}
          {task.type !== "CHECKLIST" && task.type !== "UPLOAD" && (
            <textarea className="ad-in" {...noCopy} rows={task.type === "CODE" ? 9 : task.type === "URL" ? 3 : 5} value={text} onChange={(e) => setText(e.target.value)}
              style={task.type === "CODE" ? { fontFamily: "ui-monospace, Consolas, monospace", fontSize: 14, marginTop: 8 } : { marginTop: 8 }}
              placeholder={task.type === "CODE" ? "Write or paste your code here" : task.type === "SELECT" ? "Why did you choose these?" : task.type === "URL" ? "What does your project do?" : "Type your answer here"} />)}
          {task.type === "UPLOAD" && <>
            <input className="ad-in" type="file" accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.zip,.mp4,.webm,.mov,.mp3,.m4a" onChange={(e) => setFile(e.target.files[0] || null)} />
            {sub && sub.file_url && <p className="ws-p"><a href={sub.file_url} target="_blank" rel="noreferrer">Your uploaded file ↗</a></p>}</>}
          {err && <div className="ad-alert danger" role="alert" style={{ marginTop: 10 }}>{err}</div>}
          <div className="ws-btns"><button className="ad-btn c s" disabled={busy}>{busy ? "Sending…" : sub ? "Send again" : "Submit"}</button></div>
          {sub && <p className="ws-p" style={{ fontSize: 13, color: "var(--mu2, #56667f)" }}>{sub.feedback ? `Feedback from ${sub.reviewed_by_name}: ${sub.feedback}` : "Submitted. Waiting for feedback."}</p>}
        </form>)}
      {hasQ && taskDone && !task.quiz_passed && <p className="ws-p" style={{ fontSize: 13 }}>Your task is saved. Pass the practice questions to finish the lesson.</p>}
    </div>
  );
}

const statusOf = (g, task) => (g.done ? "Completed" : task && (task.quiz_best !== null || task.submission) ? "In progress" : "Not started");
const PILL = { Completed: "ok", "In progress": "warn", "Not started": "" };

/** A lesson as one clear row: number, title, what is done, status. Click it to read the lesson and do the task. */
function GuideCard({ g, n, task, reload, next }) {
  const [open, setOpen] = useState(!!next);
  const [more, setMore] = useState(false);
  const st = statusOf(g, task);
  const hasQ = task && task.questions > 0;
  const taskDone = task && (task.type === "RECORDING" || task.type === "VOICE_TEXT" ? g.done : !!task.submission);
  const chip = (label, ok) => <span className={`ad-pill ${ok ? "ok" : ""}`} style={{ margin: 0 }}>{ok ? "✓ " : ""}{label}</span>;
  return (
    <div className="ad-card" style={{ marginBottom: 14, padding: "0 26px" }}>
      <div onClick={() => setOpen(!open)} role="button" tabIndex={0} aria-expanded={open} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setOpen(!open); } }}
        style={{ display: "flex", alignItems: "center", gap: 14, padding: "20px 0", cursor: "pointer", flexWrap: "wrap" }}>
        <span aria-hidden="true" style={{ width: 40, height: 40, borderRadius: "50%", flex: "none", display: "grid", placeItems: "center", fontWeight: 800, background: g.done ? "var(--tint-green, #dff6ea)" : "var(--n2, #0b2a45)", color: g.done ? "var(--tint-green-fg, #14703d)" : "#fff" }}>{g.done ? "✓" : n}</span>
        <span style={{ flex: "1 1 220px", minWidth: 0 }}>
          <b style={{ display: "block", fontSize: 17 }}>{g.title}</b>
          <small style={{ color: "var(--mu, #6b7a90)" }}>{KIND[g.kind]}{next && !g.done ? " · Up next" : ""}</small></span>
        {hasQ && chip("Practice", task.quiz_passed)}
        {task && chip("Task", taskDone)}
        <span className={`ad-pill ${PILL[st]}`} style={{ margin: 0 }}>{st}</span>
        <span aria-hidden="true" style={{ color: "var(--mu, #6b7a90)", width: 16, textAlign: "center" }}>{open ? "▾" : "▸"}</span>
      </div>
      {open && (
        <div style={{ paddingBottom: 24, borderTop: "1px solid var(--ln, #e6ecf4)", paddingTop: 18 }}>
          <div className="ad-eyebrow" style={{ marginBottom: 8 }}>Step 1 · Learn</div>
          {g.kind === "NOTES" && (more || g.body.length < 400 ? <p className="ws-p" style={{ whiteSpace: "pre-line" }}>{g.body}</p> : <p className="ws-p">{g.body.slice(0, 360)}…</p>)}
          {g.kind === "VIDEO" && g.file_url && <video controls preload="metadata" style={{ width: "100%", maxHeight: 460, borderRadius: 14, background: "#000", marginBottom: 12 }} src={g.file_url} />}
          {g.kind === "AUDIO" && g.file_url && <audio controls preload="metadata" style={{ width: "100%", marginBottom: 12 }} src={g.file_url} />}
          {g.kind === "PDF" && g.file_url && <p className="ws-p"><a href={g.file_url} target="_blank" rel="noreferrer">Open PDF ↗</a></p>}
          {g.kind !== "NOTES" && g.url && <p className="ws-p"><a href={g.url} target="_blank" rel="noreferrer">Open link ↗</a></p>}
          {g.kind === "NOTES" && g.body.length >= 400 && <div className="ws-btns"><button className="ad-btn o s" onClick={() => setMore(!more)}>{more ? "Show less" : "Read more"}</button></div>}
          {task && <><div className="ad-eyebrow" style={{ margin: "18px 0 0" }}>Step 2 · Practise and do the task</div><TaskBox g={g} task={task} reload={reload} /></>}
        </div>)}
    </div>
  );
}

/** Career growth tracker: goals the student sets, with a date, notes and a status they update. */
function CareerTracker() {
  const [rows, setRows] = useState(null);
  const [f, setF] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const load = useCallback(() => { all("/career-goals/").then(setRows).catch(() => setRows([])); }, []);
  useEffect(() => { load(); }, [load]);
  const save = async (e) => {
    e.preventDefault(); setErr("");
    if (!f.title.trim()) return setErr("Give your goal a title.");
    setBusy(true);
    const body = { title: f.title.trim(), target_date: f.target_date || null, notes: f.notes, status: f.status };
    try { f.id ? await api.patch(`/career-goals/${f.id}/`, body) : await api.post("/career-goals/", body); setF(null); load(); }
    catch (x) { setErr(parseError(x).message); }
    setBusy(false);
  };
  const setStatus = async (g, status) => { await api.patch(`/career-goals/${g.id}/`, { status }).catch(() => {}); load(); };
  const del = async (g) => { if (!window.confirm(`Delete the goal "${g.title}"?`)) return; await api.delete(`/career-goals/${g.id}/`).catch(() => {}); load(); };
  const total = (rows || []).length;
  const done = (rows || []).filter((g) => g.status === "DONE").length;
  const STATUS = { PLANNED: "Planned", IN_PROGRESS: "In progress", DONE: "Done" };
  return (
    <WsShell role="student" crumb="Career growth / Tracker" title="Career tracker" subtitle="Set goals, note your plan and update your progress as you go."
      action={<button className="ad-btn c" onClick={() => { setErr(""); setF({ title: "", target_date: "", notes: "", status: "PLANNED" }); }}>Add goal</button>}>
      <Tabs items={CG_TABS} />
      <Stats items={[["Goals", String(total), "You are tracking"], ["Done", String(done), "Finished"], ["Progress", total ? `${Math.round(done * 100 / total)}%` : "—", total ? "Of your goals" : "Add your first goal"]]} />
      {rows && total === 0 && <div className="ad-empty">No goals yet. Add one, for example "Learn SQL by December".</div>}
      {(rows || []).map((g) => (
        <div className="ad-card" key={g.id} style={{ marginBottom: 14 }}>
          <div className="ad-eyebrow">{STATUS[g.status]}{g.target_date ? ` · target ${g.target_date}` : ""}</div>
          <h2 style={{ margin: "8px 0" }}>{g.title}</h2>
          {g.notes && <p className="ws-p" style={{ whiteSpace: "pre-line" }}>{g.notes}</p>}
          <div className="ws-btns">
            <select className="ad-in" style={{ maxWidth: 190 }} aria-label="Status" value={g.status} onChange={(e) => setStatus(g, e.target.value)}>
              {Object.entries(STATUS).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
            <button className="ad-btn o s" onClick={() => { setErr(""); setF({ id: g.id, title: g.title, target_date: g.target_date || "", notes: g.notes, status: g.status }); }}>Edit</button>
            <button className="ad-btn o s" onClick={() => del(g)}>Delete</button>
          </div>
        </div>))}
      {f && <Modal title={f.id ? "Edit goal" : "Add a goal"} onClose={() => setF(null)}>
        <form onSubmit={save} noValidate>
          <label>Goal</label><input className="ad-in" value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} placeholder="e.g. Learn SQL" autoFocus />
          <label>Target date (optional)</label><input className="ad-in" type="date" value={f.target_date} onChange={(e) => setF({ ...f, target_date: e.target.value })} />
          <label>Status</label><select className="ad-in" value={f.status} onChange={(e) => setF({ ...f, status: e.target.value })}>{Object.entries(STATUS).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
          <label>Notes (optional)</label><textarea className="ad-in" rows={4} value={f.notes} onChange={(e) => setF({ ...f, notes: e.target.value })} />
          {err && <div className="ad-alert danger" role="alert">{err}</div>}
          <div className="ad-act" style={{ justifyContent: "flex-start", marginTop: 16 }}><button className="ad-btn p" disabled={busy}>{busy ? "Saving…" : "Save goal"}</button>
            <button type="button" className="ad-btn o" onClick={() => setF(null)}>Cancel</button></div>
        </form>
      </Modal>}
    </WsShell>
  );
}

/** Practice questions for a Job preparation tab: the topics the faculty have written questions for. */
function PracticeTopics({ sec }) {
  const [rows, setRows] = useState(null);
  useEffect(() => {
    setRows(null);
    all("/subjects/", { area: SUBJECT_AREA[sec] }).then(async (subs) => {
      const lists = await Promise.all(subs.map((s) => all("/topics/", { subject: s.id }).then((t) => t.map((x) => ({ ...x, subject: s.name })))));
      setRows(lists.flat());
    }).catch(() => setRows([]));
  }, [sec]);
  if (!rows) return null;
  return (
    <div className="ad-card" style={{ marginBottom: 20 }}><h2>Practice questions</h2>
      {rows.length === 0 ? <p className="ws-p">No practice questions have been added for this section yet.</p> : (
        <div className="ad-stream">{rows.map((t) => <div key={t.id}><small>{t.subject}</small><b>{t.name}</b><span>{t.description || "Ten random questions with explanations after you finish."}</span>
          <Link className="ad-btn c s" style={{ marginTop: 10 }} to={`/student/ecet/practice?topic=${t.id}`}>Practise</Link></div>)}</div>)}
    </div>
  );
}

/** One section of Job preparation, Career growth or Communication: lessons written by the admin, with progress. */
function GuidePage({ area, areaLabel, tabs, sec, label, roadmap }) {
  const [rows, setRows] = useState(null);
  const [tasks, setTasks] = useState({});
  const [perf, setPerf] = useState(null);
  const [filter, setFilter] = useState("all");
  const [find, setFind] = useState("");
  const load = useCallback(() => {
    all("/guides/", { area, section: sec }).then(setRows).catch(() => setRows([]));
    api.get("/quiz-performance/", { params: { area, section: sec } }).then((r) => setPerf(r.data)).catch(() => {});
    api.get("/guide-tasks/", { params: { area, section: sec } }).then((r) => setTasks(r.data)).catch(() => {});
  }, [area, sec]);
  useEffect(() => { setRows(null); load(); }, [load]);
  const total = (rows || []).length;
  const done = (rows || []).filter((g) => g.done).length;
  const groups = [...new Set((rows || []).map((g) => g.group))];
  const firstOpen = (rows || []).findIndex((g) => !g.done);
  const stat = (g) => statusOf(g, tasks[g.id]);
  const counts = { all: total, todo: (rows || []).filter((g) => stat(g) === "Not started").length, going: (rows || []).filter((g) => stat(g) === "In progress").length, done };
  const keep = (g) => (filter === "all" || (filter === "todo" && stat(g) === "Not started") || (filter === "going" && stat(g) === "In progress") || (filter === "done" && g.done)) && (!find.trim() || g.title.toLowerCase().includes(find.trim().toLowerCase()));
  return (
    <WsShell role="student" crumb={`${areaLabel} / ${label}`} title={label} subtitle={`Lessons for ${label.toLowerCase()}, added by your admin.`}>
      <Tabs items={tabs} />
      <Stats items={[["Lessons", String(total), "In this section"], ["Completed", String(done), "Completed by doing the task"], ["Progress", total ? `${Math.round(done * 100 / total)}%` : "—", total ? "Of this section" : "Nothing added yet"]]} />
      {perf && perf.topics_total > 0 && (
        <div className="ad-card" style={{ marginBottom: 20 }}><h2>Your practice performance</h2>
          <p className="ws-p">{perf.attempts ? `${perf.attempts} attempt${perf.attempts > 1 ? "s" : ""} · overall accuracy ${perf.accuracy}% · ${perf.topics_attempted} of ${perf.topics_total} topics tried.` : "You have not attempted any practice questions in this section yet."}</p>
          {perf.attempts > 0 && <div className="ad-stream">{perf.topics.filter((t) => t.attempts).map((t) => (
            <div key={t.guide_id}><small>{t.attempts} attempt{t.attempts > 1 ? "s" : ""}</small><b>{t.title}</b><span>Best {t.best}% · Last {t.last}% · Accuracy {t.accuracy}%</span></div>))}</div>}
        </div>)}
      {SUBJECT_AREA[sec] && area === "JOB_PREP" && <PracticeTopics sec={sec} />}
      {rows && total === 0 && <div className="ad-empty">Nothing has been added to {label} yet. Check back soon.</div>}
      {roadmap ? (rows || []).map((g, i) => (
        <div className={`ws-st ${g.done ? "" : i === firstOpen ? "cur" : "lock"}`} key={g.id}>
          <div className="dot"><Ic n={g.done ? "check" : i === firstOpen ? "mark" : "lock"} /></div>
          <div style={{ flex: 1 }}><small>Stage {i + 1}</small><h3>{g.title}</h3>{g.body && <p style={{ whiteSpace: "pre-line" }}>{g.body}</p>}
            {g.url && <p><a href={g.url} target="_blank" rel="noreferrer">Open link ↗</a></p>}
            {tasks[g.id] && <TaskBox g={g} task={tasks[g.id]} reload={load} />}</div>
        </div>
      )) : (<>
        {total > 0 && (
          <div className="ad-card" style={{ marginBottom: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
              <div className="ws-btns" style={{ margin: 0 }}>{[["all", "All"], ["todo", "Not started"], ["going", "In progress"], ["done", "Completed"]].map(([k, l]) => (
                <button key={k} type="button" className={`ad-btn ${filter === k ? "c" : "o"} s`} onClick={() => setFilter(k)}>{l} ({counts[k]})</button>))}</div>
              <input className="ad-in" style={{ height: 42, maxWidth: 240 }} placeholder="Search lessons" value={find} onChange={(e) => setFind(e.target.value)} /></div>
            <progress value={done} max={total || 1} style={{ width: "100%", marginTop: 16 }} />
            <small style={{ color: "var(--mu, #6b7a90)" }}>{done} of {total} lessons completed</small>
          </div>)}
        {rows && total > 0 && rows.filter(keep).length === 0 && <div className="ad-empty">No lessons match. Try another filter.</div>}
        {groups.map((grp) => {
          const inGrp = (rows || []).filter((g) => g.group === grp);
          const shown = inGrp.filter(keep);
          if (!shown.length) return null;
          return (
            <div key={grp || "all"} style={{ marginBottom: 12 }}>
              {grp && <h2 style={{ margin: "8px 0 14px" }}>{grp}<span className="ad-pill">{inGrp.filter((g) => g.done).length} of {inGrp.length} done</span></h2>}
              {shown.map((g) => <GuideCard key={g.id} g={g} n={rows.indexOf(g) + 1} task={tasks[g.id]} reload={load} next={rows.indexOf(g) === firstOpen} />)}
            </div>);
        })}
      </>)}
    </WsShell>
  );
}

/* ---------- Job preparation ---------- */
const JP_TABS = [["Aptitude", "/student/job-prep"], ["Reasoning", "/student/job-prep/reasoning"], ["Coding", "/student/job-prep/coding"], ["Technical", "/student/job-prep/technical"], ["HR", "/student/job-prep/hr"], ["Résumé", "/student/job-prep/resume"], ["Projects", "/student/job-prep/projects"]];
const JP = { aptitude: "Aptitude", reasoning: "Reasoning", coding: "Coding practice", technical: "Technical interview", hr: "HR interview", projects: "Project preparation" };

export function JobPrep() {
  const { sec } = useParams();
  if (sec === "resume") return <Resume />;
  const key = sec && JP[sec] ? sec : "aptitude";
  return <GuidePage area="JOB_PREP" areaLabel="Job preparation" tabs={JP_TABS} sec={key} label={JP[key]} />;
}

function Resume() {
  const { user } = useAuth();
  const [r, setR] = useState({ name: user.full_name, role: "", email: user.email || "", phone: user.phone || "", summary: "", skills: "", project: "", edu: "" });
  const set = (k) => (e) => setR({ ...r, [k]: e.target.value });
  const F = ({ k, l, area }) => <><label>{l}</label>{area ? <textarea className="ad-in" rows={3} value={r[k]} onChange={set(k)} /> : <input className="ad-in" value={r[k]} onChange={set(k)} />}</>;
  return (
    <WsShell role="student" crumb="Job preparation / Résumé" title="Résumé builder" subtitle="Fill the form and watch your résumé take shape." action={<Btn b={["Download PDF", null, () => window.print()]} kind="c" />}>
      <Tabs items={JP_TABS} />
      <div className="ws-split" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <div className="ad-card ws-form"><h2>Your details</h2>
          <F k="name" l="Full name" /><F k="role" l="Headline" /><F k="email" l="Email" /><F k="phone" l="Phone" />
          <F k="summary" l="Summary" area /><F k="skills" l="Skills (comma separated)" /><F k="project" l="Project" area /><F k="edu" l="Education" />
        </div>
        <div className="ws-rs ws-print">
          <h2>{r.name}</h2><p>{r.role} · {r.email} · {r.phone}</p>
          <h4>Summary</h4><p>{r.summary}</p><h4>Skills</h4><div className="ws-tags">{r.skills.split(",").filter(Boolean).map((s) => <span key={s}>{s.trim()}</span>)}</div>
          <h4>Projects</h4><p>{r.project}</p><h4>Education</h4><p>{r.edu}</p>
        </div>
      </div>
    </WsShell>
  );
}


/* ---------- Career growth ---------- */
const CG_TABS = [["Technologies", "/student/career"], ["Career paths", "/student/career/paths"], ["Roadmap", "/student/career/roadmap"], ["Projects", "/student/career/projects"], ["Tracker", "/student/career/tracker"]];
const CG = { technologies: "Technologies", paths: "Career paths", roadmap: "Roadmap", projects: "Recommended projects" };
export function Career() {
  const { sec } = useParams();
  if (sec === "tracker") return <CareerTracker />;
  const key = sec && CG[sec] ? sec : "technologies";
  return <GuidePage area="CAREER" areaLabel="Career growth" tabs={CG_TABS} sec={key} label={CG[key]} roadmap={key === "roadmap"} />;
}

/* ---------- Communication ---------- */
const CM_TABS = [["Spoken English", "/student/communication"], ["Vocabulary", "/student/communication/vocabulary"], ["Grammar", "/student/communication/grammar"], ["Speaking", "/student/communication/speaking"], ["Listening", "/student/communication/listening"], ["Group discussion", "/student/communication/gd"], ["Presentation", "/student/communication/presentation"], ["Interview", "/student/communication/interview"], ["Professional", "/student/communication/professional"]];
const CM = { spoken: "Spoken English", vocabulary: "Vocabulary", grammar: "Grammar", speaking: "Speaking practice", listening: "Listening", gd: "Group discussion", presentation: "Presentation skills", interview: "Interview communication", professional: "Professional communication" };
export function Comm() {
  const { sec } = useParams();
  const key = sec && CM[sec] ? sec : "spoken";
  return <GuidePage area="COMM" areaLabel="Communication" tabs={CM_TABS} sec={key} label={CM[key]} />;
}
