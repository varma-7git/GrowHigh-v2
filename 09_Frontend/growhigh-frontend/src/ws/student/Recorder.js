import { useCallback, useEffect, useRef, useState } from "react";
import api, { parseError } from "../../api/client";
import { Err, all } from "../../admin/ui";

const MAX = 120; // seconds
const clock = (t) => `${String(Math.floor(t / 60)).padStart(2, "0")}:${String(t % 60).padStart(2, "0")}`;
const pickType = () => ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"].find((t) => window.MediaRecorder && MediaRecorder.isTypeSupported(t)) || "";
const extOf = (t) => (t.includes("ogg") ? "ogg" : t.includes("mp4") ? "m4a" : "webm");

/** Record a spoken answer to one prompt, listen back, then save it. Saved answers are listed below with faculty feedback. */
export default function Recorder({ guide }) {
  const [state, setState] = useState("idle"); // idle | recording | review
  const [secs, setSecs] = useState(0);
  const [blob, setBlob] = useState(null);
  const [url, setUrl] = useState("");
  const [err, setErr] = useState("");
  const [saved, setSaved] = useState([]);
  const [busy, setBusy] = useState(false);
  const rec = useRef(null);
  const chunks = useRef([]);
  const timer = useRef(null);
  const stream = useRef(null);
  const supported = typeof window !== "undefined" && !!(window.MediaRecorder && navigator.mediaDevices?.getUserMedia);

  const load = useCallback(() => { all("/recordings/", { guide: guide.id }).then(setSaved).catch(() => {}); }, [guide.id]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => () => { clearInterval(timer.current); stream.current?.getTracks().forEach((t) => t.stop()); }, []);

  const stop = useCallback(() => { clearInterval(timer.current); if (rec.current && rec.current.state !== "inactive") rec.current.stop(); }, []);
  const start = async () => {
    setErr("");
    try {
      stream.current = await navigator.mediaDevices.getUserMedia({ audio: true });
      const type = pickType();
      rec.current = new MediaRecorder(stream.current, type ? { mimeType: type } : undefined);
      chunks.current = [];
      rec.current.ondataavailable = (e) => { if (e.data.size) chunks.current.push(e.data); };
      rec.current.onstop = () => {
        stream.current.getTracks().forEach((t) => t.stop());
        const b = new Blob(chunks.current, { type: rec.current.mimeType || type || "audio/webm" });
        setBlob(b); setUrl(URL.createObjectURL(b)); setState("review");
      };
      rec.current.start();
      setSecs(0); setState("recording");
      timer.current = setInterval(() => setSecs((v) => { if (v + 1 >= MAX) { stop(); return MAX; } return v + 1; }), 1000);
    } catch (e) { setErr("The microphone could not be used. Allow microphone access in your browser and try again."); }
  };
  const discard = () => { if (url) URL.revokeObjectURL(url); setBlob(null); setUrl(""); setState("idle"); setSecs(0); };
  const save = async () => {
    setBusy(true); setErr("");
    const fd = new FormData();
    fd.append("guide_id", guide.id); fd.append("seconds", secs);
    fd.append("file", blob, `speaking.${extOf(blob.type)}`);
    try { await api.post("/recordings/", fd); discard(); load(); } catch (e) { setErr(parseError(e).message); }
    setBusy(false);
  };
  const del = async (r) => { if (!window.confirm("Delete this recording?")) return; try { await api.delete(`/recordings/${r.id}/`); load(); } catch (e) { setErr(parseError(e).message); } };

  return (
    <div style={{ marginTop: 14, borderTop: "1px solid var(--ln)", paddingTop: 14 }}>
      <Err e={err} />
      {!supported ? <p className="ws-p">Recording is not supported in this browser. Try the latest Chrome, Edge, Firefox or Safari.</p> : (
        <>
          {state === "idle" && <button className="ad-btn c s" onClick={start}>● Record your answer</button>}
          {state === "recording" && <div className="ws-btns" style={{ alignItems: "center" }}><b style={{ color: "#c0392b" }}>● Recording {clock(secs)} / {clock(MAX)}</b><button className="ad-btn p s" onClick={stop}>Stop</button></div>}
          {state === "review" && (
            <div><audio controls src={url} style={{ width: "100%" }} /><div className="ws-btns"><button className="ad-btn c s" disabled={busy} onClick={save}>{busy ? "Saving…" : "Save recording"}</button><button className="ad-btn o s" onClick={discard}>Record again</button></div></div>
          )}
        </>
      )}
      {saved.length > 0 && <div style={{ marginTop: 14 }}><small style={{ color: "var(--mu)", fontWeight: 700 }}>Your saved answers</small>
        {saved.map((r) => (
          <div key={r.id} style={{ marginTop: 10 }}>
            <audio controls src={r.file_url} preload="none" style={{ width: "100%" }} />
            <div className="ad-pr"><span>{new Date(r.created_at).toLocaleString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })} · {clock(r.seconds)}</span><button className="ad-link r" onClick={() => del(r)}>Delete</button></div>
            {r.feedback ? <div className="ad-alert" style={{ marginTop: 6 }}><b>Feedback{r.reviewed_by_name ? ` from ${r.reviewed_by_name}` : ""}:</b> {r.feedback}</div> : <small style={{ color: "var(--mu)" }}>Waiting for feedback.</small>}
          </div>
        ))}</div>}
    </div>
  );
}
