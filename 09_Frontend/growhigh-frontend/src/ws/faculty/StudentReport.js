import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Panel, Stats } from "../kit";
import { Err, List, Row, Select, all } from "../../admin/ui";
import api, { parseError } from "../../api/client";

const pc = (v) => (v == null ? "—" : `${v}%`);
const day = (d) => new Date(d).toLocaleDateString("en-GB", { day: "2-digit", month: "short" });

/** One student's whole picture: tests, weak topics, and progress in Job preparation, Career growth and Communication. */
export default function StudentReport({ initial }) {
  const [q, setQ] = useState("");
  const [people, setPeople] = useState([]);
  const [pick, setPick] = useState(initial || "");
  const [rep, setRep] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => { all("/roster/", { search: q || undefined }).then(setPeople).catch(() => {}); }, [q]);
  useEffect(() => {
    setRep(null); setErr("");
    if (!pick) return;
    api.get(`/performance/student/${pick}/`).then((r) => setRep(r.data)).catch((e) => setErr(parseError(e).message));
  }, [pick]);
  const known = people.some((p) => String(p.id) === String(pick));
  const t = rep && rep.tests;
  return (
    <div className="ad-card" style={{ marginTop: 22 }}>
      <h2>Individual student performance</h2>
      <p className="ws-p">Pick a student to see their test results, weak topics and progress in Job preparation, Career growth and Communication.</p>
      <div className="ad-filters">
        <input className="ad-in" style={{ maxWidth: 260, height: 42 }} placeholder="Search by name or roll number" value={q} onChange={(e) => setQ(e.target.value)} />
        <Select value={pick} onChange={setPick} options={[["", "Choose a student"], ...(!known && rep ? [[String(pick), rep.student.name]] : []), ...people.slice(0, 60).map((p) => [String(p.id), `${p.full_name} · ${p.login_id}`])]} />
      </div>
      <Err e={err} />
      {!pick && <p className="ws-foot">Nothing selected yet.</p>}
      {rep && (<>
        <h3 style={{ margin: "6px 0 14px" }}>{rep.student.name} <small style={{ color: "var(--mu, #6b7a90)", fontWeight: 600 }}>{rep.student.login_id}</small></h3>
        <Stats items={[["Tests taken", `${t.taken}${t.assigned ? ` of ${t.assigned}` : ""}`, "Your tests"], ["Test average", pc(t.average), t.pass_rate == null ? "No tests taken yet" : `Pass rate ${t.pass_rate}%`], ["Practice sets", String(t.practice_sets), t.practice_average == null ? "ECET practice" : `Average ${t.practice_average}%`]]} />
        <div className="ad-grid g2">
          <Panel h="Weak topics in tests" p={t.weak_topics.length ? "" : "Appears once the student takes your tests."} bars={t.weak_topics.map((w) => [w.name, w.percent])} foot={t.weak_topics.length ? "Lowest scoring topics first." : ""} />
          <Panel h="Learning progress" p="" bars={rep.learning.map((a) => [`${a.label} · ${a.completed}/${a.lessons} lessons`, a.lessons ? Math.round(a.completed * 100 / a.lessons) : 0])} foot="Lessons completed by practice and hands-on tasks." />
        </div>
        <h3 style={{ margin: "22px 0 10px" }}>Practice and tasks by module</h3>
        <List head={<><span>Module</span><span>Activity</span></>} rows={rep.learning.map((a) => (
          <Row key={a.area} title={a.label} meta={`${a.completed} of ${a.lessons} lessons completed`}>
            <span className="ad-hint">{a.quiz_attempts ? `${a.quiz_attempts} practice attempt${a.quiz_attempts > 1 ? "s" : ""} · accuracy ${pc(a.accuracy)}` : "No practice yet"} · {a.submissions} answer{a.submissions === 1 ? "" : "s"} submitted</span>
            {a.waiting > 0 && <span className="ad-pill warn">{a.waiting} waiting for feedback</span>}
          </Row>))} />
        {rep.weak_lessons.length > 0 && (<>
          <h3 style={{ margin: "22px 0 10px" }}>Needs attention (lowest practice accuracy)</h3>
          <List head={<><span>Lesson</span><span>Accuracy</span></>} rows={rep.weak_lessons.map((w) => (
            <Row key={w.title} title={w.title} meta={`${w.attempts} attempt${w.attempts > 1 ? "s" : ""}`}><span className={`ad-pill ${w.accuracy < 40 ? "bad" : w.accuracy < 70 ? "warn" : "ok"}`}>{w.accuracy}%</span></Row>))} />
        </>)}
        <h3 style={{ margin: "22px 0 10px" }}>Test results</h3>
        <List head={<><span>Test</span><span>Score</span></>} empty="This student has not taken any of your tests yet." rows={t.results.map((r, i) => (
          <Row key={i} title={r.name} meta={r.date ? day(r.date) : ""}><span className="ad-hint">{r.score}/{r.total} · {r.percent}%</span><span className={`ad-pill ${r.passed ? "ok" : "bad"}`}>{r.passed ? "Pass" : "Needs help"}</span></Row>))} />
        <h3 style={{ margin: "22px 0 10px" }}>Recent answers and tasks</h3>
        <List head={<><span>Lesson</span><span>Status</span></>} empty="No written, uploaded or spoken answers yet." rows={rep.recent.map((r, i) => (
          <Row key={i} title={r.title} meta={`${r.type} · ${day(r.at)}${r.feedback ? ` · Feedback: ${r.feedback}` : ""}`}><span className={`ad-pill ${r.reviewed ? "ok" : "warn"}`}>{r.reviewed ? "Reviewed" : "Waiting for feedback"}</span></Row>))} />
        <div className="ws-btns"><Link to="/faculty/reviews" className="ad-btn o s">Open student reviews</Link></div>
      </>)}
    </div>
  );
}
