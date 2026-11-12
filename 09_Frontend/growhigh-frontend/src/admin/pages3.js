import { useCallback, useEffect, useState } from "react";
import api, { parseError } from "../api/client";
import { AdminShell, Err, List, Modal, Row, Search, Select, Stat, all } from "./ui";

const L = ["A", "B", "C", "D"];
const SL = <span className="ad-sl">/</span>;
const TYPES = { DAILY: "Daily", WEEKLY: "Weekly", CUMULATIVE: "Cumulative", MOCK: "Mock" };
const STATUS = { UPCOMING: ["Upcoming", "warn"], ACTIVE: ["Running", "ok"], ENDED: ["Ended", ""] };

export function QuestionBank({ message, notify }) {
  const [rows, setRows] = useState([]);
  const [subs, setSubs] = useState([]);
  const [q, setQ] = useState("");
  const [sub, setSub] = useState("");
  const [open, setOpen] = useState(null);
  useEffect(() => { all("/subjects/", { area: "ALL" }).then(setSubs).catch(() => {}); }, []);
  const load = useCallback(() => { all("/questions/", { search: q || undefined, subject: sub || undefined }).then(setRows).catch((e) => notify(parseError(e).message, "danger")); }, [q, sub, notify]);
  useEffect(() => { load(); }, [load]);
  const hide = async (x) => { try { await api.patch(`/questions/${x.id}/`, { is_active: !x.is_active }); load(); } catch (e) { notify(parseError(e).message, "danger"); } };
  const del = async (x) => {
    if (!window.confirm("Delete this question? This cannot be undone.")) return;
    try { await api.delete(`/questions/${x.id}/`); notify("Question deleted.", "success"); load(); } catch (e) { notify(parseError(e).message, "danger"); }
  };
  return (
    <AdminShell title="Question bank oversight" crumb="Question bank" subtitle="Maintain clarity, provenance and quality across faculty-authored questions." message={message}>
      <div className="ad-grid g3">
        <Stat label="Questions" value={rows.length} note="Matching your search" />
        <Stat label="Contributors" value={new Set(rows.map((r) => r.created_by_name)).size} note="People who added questions" />
        <Stat label="Hidden" value={rows.filter((r) => !r.is_active).length} note="Not available for new tests" />
      </div>
      <div className="ad-filters"><Search value={q} onChange={setQ} placeholder="Search question text or topic" /><Select value={sub} onChange={setSub} options={[["", "All subjects"], ...subs.map((s) => [String(s.id), s.name])]} /></div>
      <List head="Question / Subject / Added by / Actions" empty="No questions yet. Faculty add them from their workspace." rows={rows.map((x) => (
        <div key={x.id}>
          <Row title={<span style={{ cursor: "pointer" }} onClick={() => setOpen(open === x.id ? null : x.id)}>{x.text}{!x.is_active && <span className="ad-pill bad">Hidden</span>}</span>} meta={`${x.subject_name} · ${x.topic_name} · ${x.created_by_name || "Unknown"}`}>
            <button className="ad-link" onClick={() => setOpen(open === x.id ? null : x.id)}>{open === x.id ? "Close" : "View"}</button>{SL}
            <button className="ad-link" onClick={() => hide(x)}>{x.is_active ? "Hide" : "Show"}</button>{SL}
            <button className="ad-link r" onClick={() => del(x)}>Delete</button></Row>
          {open === x.id && <div style={{ padding: "0 4px 18px" }}>{x.options.map((o, i) => <div key={i} style={{ padding: "4px 0", fontWeight: i === x.correct ? 700 : 400, color: i === x.correct ? "#14703d" : "inherit" }}>{L[i]}. {o}{i === x.correct ? " ✓" : ""}</div>)}
            {x.explanation && <p style={{ color: "var(--mu, #6b7a90)" }}>{x.explanation}</p>}</div>}
        </div>))} />
      <div className="ad-card" style={{ marginTop: 24 }}><h2>Quality over quantity</h2><p style={{ color: "var(--mu, #6b7a90)" }}>Review one correct answer, plausible distractors, clear topic mapping and a useful explanation. A question used in a test cannot be deleted: hide it instead.</p></div>
    </AdminShell>
  );
}

export function AdminTests({ message, notify }) {
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const [type, setType] = useState("");
  const load = useCallback(() => { all("/tests/", { search: q || undefined, test_type: type || undefined }).then(setRows).catch((e) => notify(parseError(e).message, "danger")); }, [q, type, notify]);
  useEffect(() => { load(); }, [load]);
  const del = async (t) => {
    if (!window.confirm(`Delete ${t.name}? This cannot be undone.`)) return;
    try { await api.delete(`/tests/${t.id}/`); notify("Test deleted.", "success"); load(); } catch (e) { notify(parseError(e).message, "danger"); }
  };
  const count = (s) => rows.filter((r) => r.status === s).length;
  return (
    <AdminShell title="Test management" crumb="Tests" subtitle="See assessment coverage, schedules and completion across the platform." message={message}>
      <div className="ad-grid g3">
        <Stat label="Scheduled" value={count("UPCOMING")} note="Not started yet" />
        <Stat label="Active" value={count("ACTIVE")} note="Running now" />
        <Stat label="Completed" value={count("ENDED")} note="Finished" />
      </div>
      <div className="ad-filters"><Search value={q} onChange={setQ} placeholder="Search assessment name" /><Select value={type} onChange={setType} options={[["", "All types"], ...Object.entries(TYPES)]} /></div>
      <List head="Test / Type / Date / Branch / Year / Status / Action" empty="No tests yet. Faculty create them from their workspace." rows={rows.map((t) => (
        <Row key={t.id} title={<>{t.name}<span className={`ad-pill ${STATUS[t.status][1]}`}>{STATUS[t.status][0]}</span></>}
          meta={`${TYPES[t.test_type]} · ${t.scheduled_date} ${t.start_time.slice(0, 5)} · ${t.branch_code || "All branches"} · ${t.year_of_study ? `Year ${t.year_of_study}` : "All years"} · ${t.question_count} questions · ${t.assigned_count} students · by ${t.created_by_name || "—"}`}>
          <button className="ad-link r" onClick={() => del(t)}>Delete</button></Row>))} />
      <div className="ad-card" style={{ marginTop: 24 }}><h2>Consistent rules, clearer expectations</h2><p style={{ color: "var(--mu, #6b7a90)" }}>Assigned tests allow one attempt. AP ECET mocks use 200 questions, 200 marks, 3 hours and no negative marking.</p></div>
    </AdminShell>
  );
}

export function AdminPapers({ message, notify }) {
  const [rows, setRows] = useState([]);
  const [branches, setBranches] = useState([]);
  const [f, setF] = useState(null);
  const [er, setEr] = useState({});
  const [busy, setBusy] = useState(false);
  const load = useCallback(() => { all("/papers/").then(setRows).catch((e) => notify(parseError(e).message, "danger")); }, [notify]);
  useEffect(() => { load(); all("/branches/").then(setBranches).catch(() => {}); }, [load]);
  const save = async (e) => {
    e.preventDefault(); setEr({}); setBusy(true);
    const fd = new FormData();
    fd.append("year", f.year); fd.append("title", f.title);
    if (f.branch_id) fd.append("branch_id", f.branch_id);
    if (f.file) fd.append("file", f.file);
    try {
      if (f.id) {   // edit: change year, title or branch; a new PDF is optional
        if (f.file) { if (!f.branch_id) fd.append("branch_id", ""); await api.patch(`/papers/${f.id}/`, fd); }
        else await api.patch(`/papers/${f.id}/`, { year: f.year, title: f.title, branch_id: f.branch_id ? Number(f.branch_id) : null });
        notify("Paper updated.", "success");
      } else { await api.post("/papers/", fd); notify("Paper added.", "success"); }
      setF(null); load();
    }
    catch (x) { const p2 = parseError(x); setEr(p2.fields || {}); notify(p2.message, "danger"); }
    setBusy(false);
  };
  const edit = (r) => { setF({ id: r.id, year: String(r.year), title: r.title, branch_id: r.branch_id ? String(r.branch_id) : "", file: null }); };
  const toggle = async (r) => { try { await api.patch(`/papers/${r.id}/`, { is_active: !r.is_active }); load(); } catch (x) { notify(parseError(x).message, "danger"); } };
  const del = async (r) => {
    if (!window.confirm(`Delete ${r.title}? Students who saved it will lose it.`)) return;
    try { await api.delete(`/papers/${r.id}/`); notify("Paper deleted.", "success"); load(); } catch (x) { notify(parseError(x).message, "danger"); }
  };
  return (
    <AdminShell title="Previous papers" crumb="Previous papers" subtitle="Upload earlier AP ECET papers as PDFs for students to open and save." message={message}>
      <div className="ad-grid g3">
        <Stat label="Papers" value={rows.length} note="Uploaded so far" />
        <Stat label="Visible" value={rows.filter((r) => r.is_active).length} note="Shown to students" />
        <Stat label="Hidden" value={rows.filter((r) => !r.is_active).length} note="Not shown" />
      </div>
      <List head="Paper / Branch / Action" empty="No papers yet. Add the first one." rows={rows.map((r) => (
        <Row key={r.id} title={<>{r.title}{!r.is_active && <span className="ad-pill bad">Hidden</span>}</>} meta={`${r.year} · ${r.branch_code || "All branches"}`}>
          <a className="ad-link" href={r.file_url} target="_blank" rel="noreferrer">Open</a>{SL}<button className="ad-link" onClick={() => edit(r)}>Edit</button>{SL}<button className="ad-link" onClick={() => toggle(r)}>{r.is_active ? "Hide" : "Show"}</button>{SL}<button className="ad-link r" onClick={() => del(r)}>Delete</button></Row>))} />
      <div className="ad-card" style={{ marginTop: 24 }}><h2>Add a paper</h2>
        <button className="ad-btn o" onClick={() => setF({ year: "", title: "", branch_id: "", file: null })}>Add paper</button></div>
      {f && <Modal title={f.id ? "Edit paper" : "Add a paper"} onClose={() => setF(null)}>
        <form onSubmit={save}>
            <label>Year</label><input className="ad-in" type="number" value={f.year} onChange={(e) => setF({ ...f, year: e.target.value })} /><Err e={er.year} />
            <label>Title</label><input className="ad-in" placeholder="AP ECET 2023 · Computer Science" value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /><Err e={er.title} />
            <label>Branch</label><select className="ad-in" value={f.branch_id} onChange={(e) => setF({ ...f, branch_id: e.target.value })}><option value="">All branches</option>{branches.map((b) => <option key={b.id} value={b.id}>{b.code}</option>)}</select>
            <label>{f.id ? "Replace PDF (optional, up to 25 MB)" : "PDF file (up to 25 MB)"}</label><input className="ad-in" type="file" accept="application/pdf,.pdf" onChange={(e) => setF({ ...f, file: e.target.files[0] })} /><Err e={er.file} />
            <div className="ad-act" style={{ justifyContent: "flex-start", marginTop: 14 }}><button className="ad-btn p" disabled={busy}>{busy ? "Uploading…" : "Save"}</button><button type="button" className="ad-btn o" onClick={() => setF(null)}>Cancel</button></div>
          </form>
      </Modal>}
    </AdminShell>
  );
}

const AREAS = {
  JOB_PREP: ["Job preparation", [["aptitude", "Aptitude"], ["reasoning", "Reasoning"], ["coding", "Coding"], ["technical", "Technical interview"], ["hr", "HR interview"], ["projects", "Projects"]]],
  CAREER: ["Career growth", [["technologies", "Technologies"], ["paths", "Career paths"], ["roadmap", "Roadmap (one lesson per stage, in order)"], ["projects", "Projects"]]],
  COMM: ["Communication", [["spoken", "Spoken English"], ["vocabulary", "Vocabulary"], ["grammar", "Grammar"], ["speaking", "Speaking"], ["listening", "Listening"], ["gd", "Group discussion"], ["presentation", "Presentation"], ["interview", "Interview"], ["professional", "Professional"]]],
};
const GKIND = [["NOTES", "Written notes"], ["VIDEO", "Video"], ["AUDIO", "Audio"], ["PDF", "PDF"], ["LINK", "Web link"]];

/** Questions on one lesson. A student completes the lesson by scoring 40% or more on them. */
function LessonQuestions({ g, notify, onClose }) {
  const blank = { qtype: "MCQ", text: "", options: ["", "", "", ""], correct: 0, answer: "", explanation: "" };
  const [rows, setRows] = useState(null);
  const [f, setF] = useState(blank);
  const [er, setEr] = useState("");
  const [busy, setBusy] = useState(false);
  const [cfg, setCfg] = useState({ task_type: "", prompt: "", options: [] });
  const [subs, setSubs] = useState([]);
  const load = useCallback(() => {
    all("/guide-questions/", { guide: g.id }).then(setRows).catch(() => setRows([]));
    api.get(`/guides/${g.id}/task-setting/`).then((r) => setCfg(r.data)).catch(() => {});
    all("/guide-submissions/", { guide: g.id }).then(setSubs).catch(() => {});
  }, [g.id]);
  useEffect(() => { load(); }, [load]);
  const saveCfg = async () => {
    try { await api.put(`/guides/${g.id}/task-setting/`, { ...cfg, options: (cfg.options || []).filter((o) => o.trim()) }); notify("Task saved.", "success"); }
    catch (x) { const p = parseError(x); setEr(Object.values(p.fields || {}).flat().join(" ") || p.message); }
  };
  const setOpt = (i, v) => setF({ ...f, options: f.options.map((o, k) => (k === i ? v : o)) });
  const add = async (e) => {
    e.preventDefault(); setEr(""); setBusy(true);
    try { await api.post("/guide-questions/", { guide_id: g.id, qtype: f.qtype, text: f.text, options: f.qtype === "MCQ" ? f.options : [], correct: Number(f.correct), answer: f.answer, explanation: f.explanation, order_no: (rows || []).length }); setF(blank); load(); notify("Question added.", "success"); }
    catch (x) { const p = parseError(x); setEr(Object.values(p.fields || {}).flat().join(" ") || p.message); }
    setBusy(false);
  };
  const del = async (q) => { if (!window.confirm("Delete this question?")) return; try { await api.delete(`/guide-questions/${q.id}/`); load(); } catch (x) { notify(parseError(x).message, "danger"); } };
  return (
    <Modal title={`Questions: ${g.title}`} onClose={onClose}>
      <h3 style={{ margin: "0 0 6px" }}>Student task</h3>
      <p className="ws-p" style={{ margin: "0 0 8px" }}>Students answer the practice questions below and also do this hands-on task. Choose the kind of task that suits the topic.</p>
      <select className="ad-in" value={cfg.task_type} onChange={(e) => setCfg({ ...cfg, task_type: e.target.value })}>
        <option value="">Default ({g.area === "COMM" && g.section === "speaking" ? "record a spoken answer" : "write an answer"})</option>
        <option value="WRITTEN">Write an answer</option><option value="CODE">Write code</option><option value="UPLOAD">Upload a file or video</option>
        <option value="URL">Share a link (GitHub)</option><option value="SELECT">Choose from a list and explain</option><option value="CHECKLIST">Tick every step on a checklist</option>
        {g.area !== "CAREER" && <><option value="RECORDING">Record a spoken answer</option><option value="VOICE_TEXT">Record and also write an answer</option></>}</select>
      {(cfg.task_type === "SELECT" || cfg.task_type === "CHECKLIST") && (
        <textarea className="ad-in" rows={5} placeholder="One item per line, e.g. Python" value={(cfg.options || []).join("\n")} onChange={(e) => setCfg({ ...cfg, options: e.target.value.split("\n") })} style={{ marginTop: 8 }} />)}
      <textarea className="ad-in" rows={2} placeholder="Instruction for the student, e.g. Upload your project report" value={cfg.prompt} onChange={(e) => setCfg({ ...cfg, prompt: e.target.value })} style={{ marginTop: 8 }} />
      <button type="button" className="ad-btn o" style={{ marginTop: 8 }} disabled={!cfg.task_type} onClick={saveCfg}>Save task</button>
      <p className="ws-p" style={{ margin: "14px 0 0" }}>{subs.length} written answer{subs.length === 1 ? "" : "s"} or upload{subs.length === 1 ? "" : "s"} so far. Faculty give feedback under Student reviews.</p>
      <h3 style={{ margin: "18px 0 6px" }}>Questions</h3>
      {rows && rows.length === 0 && <p className="ws-p">No questions yet. Students will do the task above instead.</p>}
      {(rows || []).map((q, i) => (
        <div key={q.id} style={{ padding: "10px 0", borderBottom: "1px solid var(--ln, #e3e9f1)" }}>
          <b>{i + 1}. {q.text}</b>
          <div style={{ fontSize: 13, color: "var(--mu2, #56667f)" }}>{q.qtype === "NUMERIC" ? `Answer: ${q.answer}` : q.options.map((o, k) => `${"ABCD"[k]}. ${o}${k === q.correct ? " ✓" : ""}`).join("   ")}</div>
          <button className="ad-link r" onClick={() => del(q)}>Delete</button>
        </div>))}
      <form onSubmit={add} noValidate style={{ marginTop: 18 }}>
        <h3 style={{ margin: "0 0 8px" }}>Add a question</h3>
        <label>Question</label><textarea className="ad-in" rows={2} value={f.text} onChange={(e) => setF({ ...f, text: e.target.value })} />
        <label>Type of question</label><select className="ad-in" value={f.qtype} onChange={(e) => setF({ ...f, qtype: e.target.value })}><option value="MCQ">Multiple choice</option><option value="NUMERIC">Numerical answer</option></select>
        {f.qtype === "NUMERIC" ? <><label>Correct answer (a number)</label><input className="ad-in" inputMode="decimal" value={f.answer} onChange={(e) => setF({ ...f, answer: e.target.value })} /></> : <>
        {[0, 1, 2, 3].map((i) => <div key={i}><label>Option {"ABCD"[i]}</label><input className="ad-in" value={f.options[i]} onChange={(e) => setOpt(i, e.target.value)} /></div>)}
        <label>Correct option</label><select className="ad-in" value={f.correct} onChange={(e) => setF({ ...f, correct: e.target.value })}>{"ABCD".split("").map((l, i) => <option key={l} value={i}>{l}</option>)}</select></>}
        <label>Explanation (shown after answering)</label><textarea className="ad-in" rows={2} value={f.explanation} onChange={(e) => setF({ ...f, explanation: e.target.value })} />
        {er && <div className="ad-alert danger" role="alert" style={{ marginTop: 10 }}>{er}</div>}
        <div className="ad-act" style={{ justifyContent: "flex-start", marginTop: 14 }}><button className="ad-btn p" disabled={busy}>{busy ? "Saving…" : "Add question"}</button>
          <button type="button" className="ad-btn o" onClick={onClose}>Close</button></div>
      </form>
    </Modal>
  );
}

export function AdminContent({ message, notify }) {
  const [area, setArea] = useState("JOB_PREP");
  const [sec, setSec] = useState("aptitude");
  const [rows, setRows] = useState([]);
  const [all2, setAll2] = useState([]);
  const [f, setF] = useState(null);
  const [qg, setQg] = useState(null);
  const [er, setEr] = useState({});
  const [busy, setBusy] = useState(false);
  const load = useCallback(() => {
    all("/guides/", { area, section: sec }).then(setRows).catch((e) => notify(parseError(e).message, "danger"));
    all("/guides/").then(setAll2).catch(() => {});
  }, [area, sec, notify]);
  useEffect(() => { load(); }, [load]);
  const pickArea = (a) => { setArea(a); setSec(AREAS[a][1][0][0]); setF(null); };
  const save = async (e) => {
    e.preventDefault(); setEr({}); setBusy(true);
    const fd = new FormData();
    fd.append("area", area); fd.append("section", sec); fd.append("group", f.group); fd.append("kind", f.kind); fd.append("title", f.title);
    fd.append("body", f.kind === "NOTES" ? f.body : ""); fd.append("url", f.kind === "NOTES" ? "" : f.url); fd.append("order_no", f.order_no || 0);
    if (f.file) fd.append("file", f.file);
    try { f.id ? await api.patch(`/guides/${f.id}/`, fd) : await api.post("/guides/", fd); notify("Lesson saved.", "success"); setF(null); load(); }
    catch (x) { const p2 = parseError(x); setEr(p2.fields || {}); notify(p2.message, "danger"); }
    setBusy(false);
  };
  const toggle = async (g) => { try { await api.patch(`/guides/${g.id}/`, { is_active: !g.is_active }); load(); } catch (x) { notify(parseError(x).message, "danger"); } };
  const del = async (g) => {
    if (!window.confirm(`Delete ${g.title}? Students' progress on it is removed too.`)) return;
    try { await api.delete(`/guides/${g.id}/`); notify("Lesson deleted.", "success"); load(); } catch (x) { notify(parseError(x).message, "danger"); }
  };
  const count = (a) => all2.filter((g) => g.area === a).length;
  return (
    <AdminShell title="Content & settings" crumb="Content & settings" subtitle="Write the lessons students see in Job preparation, Career growth and Communication." message={message}>
      <div className="ad-grid g3">{Object.entries(AREAS).map(([k, [l]]) => <Stat key={k} label={l} value={count(k)} note="Lessons added" />)}</div>
      <div className="ad-filters">
        <Select value={area} onChange={pickArea} options={Object.entries(AREAS).map(([k, [l]]) => [k, l])} />
        <Select value={sec} onChange={(v) => { setSec(v); setF(null); }} options={AREAS[area][1]} />
      </div>
      <List head="Lesson / Type / Action" empty="No lessons in this section yet." rows={rows.map((g) => (
        <Row key={g.id} title={<>{g.title}{!g.is_active && <span className="ad-pill bad">Hidden</span>}</>} meta={`${GKIND.find((k) => k[0] === g.kind)?.[1]}${g.group ? ` · ${g.group}` : ""} · order ${g.order_no}`}>
          <button className="ad-link" onClick={() => setF({ id: g.id, group: g.group, kind: g.kind, title: g.title, body: g.body, url: g.url, order_no: g.order_no, file: null })}>Edit</button>{SL}
          <button className="ad-link" onClick={() => setQg(g)}>Questions</button>{SL}
          <button className="ad-link" onClick={() => toggle(g)}>{g.is_active ? "Hide" : "Show"}</button>{SL}<button className="ad-link r" onClick={() => del(g)}>Delete</button></Row>))} />
      {qg && <LessonQuestions g={qg} notify={notify} onClose={() => setQg(null)} />}
      <div className="ad-act" style={{ justifyContent: "flex-start", marginTop: 24 }}>
        <button className="ad-btn o" onClick={() => setF({ group: "", kind: "NOTES", title: "", body: "", url: "", order_no: rows.length, file: null })}>Add lesson to {AREAS[area][1].find((x) => x[0] === sec)?.[1]}</button></div>
      {f && <Modal title={f.id ? "Edit lesson" : "Add a lesson"} onClose={() => setF(null)}>
          <form onSubmit={save} className="ad-form">
            <label>Type</label><select className="ad-in" value={f.kind} onChange={(e) => setF({ ...f, kind: e.target.value })}>{GKIND.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
            <label>Title</label><input className="ad-in" value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /><Err e={er.title} />
            <label>Heading inside the section (optional)</label><input className="ad-in" placeholder="e.g. Quantitative" value={f.group} onChange={(e) => setF({ ...f, group: e.target.value })} />
            {f.kind === "NOTES" ? <><label>Notes</label><textarea className="ad-in" rows={8} value={f.body} onChange={(e) => setF({ ...f, body: e.target.value })} /><Err e={er.body} /></>
              : <><label>Link</label><input className="ad-in" placeholder="https://" value={f.url} onChange={(e) => setF({ ...f, url: e.target.value })} /><Err e={er.url} />
                {(f.kind === "VIDEO" || f.kind === "PDF" || f.kind === "AUDIO") && <><label>Or upload a file ({f.kind === "VIDEO" ? "MP4, WebM or MOV, up to 300 MB" : f.kind === "AUDIO" ? "MP3, M4A, WAV or OGG, up to 50 MB" : "PDF, up to 25 MB"})</label><input className="ad-in" type="file" accept={f.kind === "VIDEO" ? "video/*" : f.kind === "AUDIO" ? "audio/*" : "application/pdf"} onChange={(e) => setF({ ...f, file: e.target.files[0] })} /><Err e={er.file} /></>}</>}
            <label>Order (smaller shows first)</label><input className="ad-in" type="number" value={f.order_no} onChange={(e) => setF({ ...f, order_no: e.target.value })} />
            <div className="ad-act" style={{ justifyContent: "flex-start", marginTop: 14 }}><button className="ad-btn p" disabled={busy}>{busy ? "Saving…" : "Save"}</button><button type="button" className="ad-btn o" onClick={() => setF(null)}>Cancel</button></div>
          </form>
      </Modal>}
    </AdminShell>
  );
}
