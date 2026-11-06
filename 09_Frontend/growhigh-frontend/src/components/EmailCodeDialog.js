import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import api, { parseError } from "../api/client";
import OtpInput from "./OtpInput";

/** Opens when the user presses Register: emails a 6-digit code to the address and waits for it.
 *  If the code cannot be delivered, the error is shown and nothing is created. */
export default function EmailCodeDialog({ email, onVerified, onCancel }) {
  const [phase, setPhase] = useState("sending");  // sending | ready | failed
  const [code, setCode] = useState(""); const [msg, setMsg] = useState(""); const [busy, setBusy] = useState(false); const [wait, setWait] = useState(0);

  const send = useCallback(async () => {
    setPhase("sending"); setMsg("");
    try { await api.post("/auth/send-email-code/", { email }, { skipAuth: true }); setPhase("ready"); setWait(30); }
    catch (e) { const p = parseError(e); setMsg(p.fields?.email || p.message); setPhase("failed"); }
  }, [email]);
  const box = useRef(null);
  useEffect(() => { send(); }, [send]);
  useEffect(() => {                     // keep the keyboard inside the dialog, and give focus back when it closes
    const before = document.activeElement;
    const trap = (e) => {
      if (e.key !== "Tab" || !box.current) return;
      const items = box.current.querySelectorAll("button:not([disabled]),input:not([disabled])");
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", trap);
    return () => { document.removeEventListener("keydown", trap); if (before && before.focus) before.focus(); };
  }, []);
  useEffect(() => { if (wait <= 0) return undefined; const t = setTimeout(() => setWait(wait - 1), 1000); return () => clearTimeout(t); }, [wait]);
  useEffect(() => { const k = (e) => e.key === "Escape" && onCancel(); window.addEventListener("keydown", k); return () => window.removeEventListener("keydown", k); }, [onCancel]);

  const verify = async (e) => {
    e.preventDefault(); setBusy(true); setMsg("");
    try { const { data } = await api.post("/auth/verify-email-code/", { email, code: code.trim() }, { skipAuth: true }); onVerified(data.token); }
    catch (x) { setMsg(parseError(x).message); setBusy(false); }
  };

  return createPortal(
    <div className="gh-dlg" onMouseDown={(e) => e.target === e.currentTarget && onCancel()}>
      <form ref={box} role="dialog" aria-modal="true" className="gh-dlg-box gh-otp-card" onSubmit={verify} aria-labelledby="otp-title">
        <div className="gh-otp-icon" aria-hidden="true"><svg width="30" height="30" viewBox="0 0 24 24" fill="currentColor"><path d="M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm0 4.2-8 5-8-5V6l8 5 8-5v2.2z"/></svg></div>
        <h3 id="otp-title">Verify your email</h3>
        {phase === "sending" && <p><span className="gh-spin" /> Sending a code to <b>{email}</b>…</p>}
        {phase === "failed" && <><div className="gh-error" style={{ fontSize: 15 }}>{msg}</div>
          <div className="d-flex gap-2 mt-3"><button type="button" className="gh-btn gh-btn-coral gh-btn-sm" onClick={send}>Try again</button>
            <button type="button" className="gh-btn gh-btn-dark gh-btn-sm" onClick={onCancel}>Change email</button></div></>}
        {phase === "ready" && <>
          <p className="gh-otp-sub">Please enter the 6-digit code we sent to<br /><b>{email}</b></p>
          <OtpInput value={code} onChange={setCode} autoFocus disabled={busy} />
          {msg && <div className="gh-error" role="alert">{msg}</div>}
          <button className="gh-btn gh-btn-coral gh-otp-confirm" disabled={busy || code.length !== 6}>{busy ? "Checking…" : "Confirm"}</button>
          <div className="gh-otp-links">
            <button type="button" className="gh-link-btn" disabled={wait > 0 || busy} onClick={send}>{wait > 0 ? `Resend code in ${wait}s` : "Resend code"}</button>
            <button type="button" className="gh-link-btn" onClick={onCancel}>Change email</button></div>
          <p className="gh-otp-note">Check your spam folder if you do not see the email.</p></>}
      </form>
    </div>, document.body);
}
