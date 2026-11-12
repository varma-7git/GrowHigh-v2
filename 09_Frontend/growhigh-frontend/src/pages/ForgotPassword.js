import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link, useNavigate } from "react-router-dom";
import Field from "../components/Field";
import OtpInput from "../components/OtpInput";
import { AuthFrame } from "../components/Public";
import api, { parseError } from "../api/client";

const MAIL = <path d="M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm0 4.2-8 5-8-5V6l8 5 8-5v2.2z" />;
const LOCK = <path d="M18 8h-1V6a5 5 0 0 0-10 0v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2zM9 6a3 3 0 0 1 6 0v2H9V6z" />;

/** Shared popup shell: Escape closes, Tab stays inside, focus returns to the page when closed. */
function Modal({ titleId, icon, onClose, onSubmit, children }) {
  const box = useRef(null);
  useEffect(() => {
    const before = document.activeElement;
    const key = (e) => {
      if (e.key === "Escape") { onClose(); return; }
      if (e.key !== "Tab" || !box.current) return;
      const items = box.current.querySelectorAll("button:not([disabled]),input:not([disabled])");
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", key);
    return () => { document.removeEventListener("keydown", key); if (before && before.focus) before.focus(); };
  }, [onClose]);
  return createPortal(
    <div className="gh-dlg" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <form ref={box} role="dialog" aria-modal="true" aria-labelledby={titleId} className="gh-dlg-box gh-otp-card" onSubmit={onSubmit} noValidate>
        <div className="gh-otp-icon" aria-hidden="true"><svg width="30" height="30" viewBox="0 0 24 24" fill="currentColor">{icon}</svg></div>
        {children}
      </form>
    </div>,
    document.body
  );
}

/** Popup 1: the six boxes. Only a correct code opens popup 2. */
function CodeDialog({ loginId, onClose, onVerified, onResend, wait }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (code.length !== 6) return setError("Enter the 6-digit code from your email.");
    setBusy(true);
    try {
      const { data } = await api.post("/auth/verify-reset-code/", { login_id: loginId, code }, { skipAuth: true });
      onVerified(data.token);
    } catch (err) {
      setError(parseError(err).message); setBusy(false);
    }
  };

  return (
    <Modal titleId="code-title" icon={MAIL} onClose={onClose} onSubmit={submit}>
      <h3 id="code-title">Verify your email</h3>
      <p className="gh-otp-sub">If that email is registered, we sent a 6-digit code to it.</p>
      <OtpInput value={code} onChange={setCode} autoFocus disabled={busy} label="Reset code" />
      {error && <div className="gh-error" role="alert">{error}</div>}
      <button className="gh-btn gh-btn-coral gh-otp-confirm" disabled={busy}>{busy ? "Checking…" : "Verify code"}</button>
      <div className="gh-otp-links">
        <button type="button" className="gh-link-btn" disabled={wait > 0 || busy} onClick={onResend}>{wait > 0 ? `Resend code in ${wait}s` : "Resend code"}</button>
        <button type="button" className="gh-link-btn" onClick={onClose}>Change email</button>
      </div>
      <p className="gh-otp-note">The code works for 10 minutes. Check your spam folder if you do not see the email.</p>
    </Modal>
  );
}

/** Popup 2: opens only after the code was verified. */
function PasswordDialog({ token, onClose, onDone }) {
  const [form, setForm] = useState({ new_password: "", confirm_password: "" });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setMessage(""); setErrors({});
    const errs = {};
    if (form.new_password.length < 8) errs.new_password = "Use at least 8 characters.";
    else if (!/[A-Za-z]/.test(form.new_password) || !/\d/.test(form.new_password)) errs.new_password = "Use at least one letter and one number.";
    if (form.confirm_password !== form.new_password) errs.confirm_password = "Passwords do not match.";
    if (Object.keys(errs).length) return setErrors(errs);
    setBusy(true);
    try {
      await api.post("/auth/reset-password/", { ...form, token }, { skipAuth: true });
      onDone();
    } catch (err) {
      const { message: m, fields } = parseError(err);
      setErrors(fields || {}); setMessage(m); setBusy(false);
    }
  };

  return (
    <Modal titleId="pw-title" icon={LOCK} onClose={onClose} onSubmit={submit}>
      <h3 id="pw-title">Set a new password</h3>
      <p className="gh-otp-sub">Your email is verified. Choose a new password.</p>
      <div style={{ textAlign: "left", marginTop: 6 }}>
        <Field label="New password" name="new_password" type="password" value={form.new_password} onChange={set}
          error={errors.new_password} hint="At least 8 characters, with a letter and a number." autoComplete="new-password" autoFocus />
        <Field label="Confirm new password" name="confirm_password" type="password" value={form.confirm_password}
          onChange={set} error={errors.confirm_password} autoComplete="new-password" />
      </div>
      {message && <div className="gh-error" role="alert">{message}</div>}
      <button className="gh-btn gh-btn-coral gh-otp-confirm" disabled={busy}>{busy ? "Saving…" : "Change password"}</button>
      <div className="gh-otp-links"><button type="button" className="gh-link-btn" onClick={onClose}>Cancel</button></div>
    </Modal>
  );
}

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [loginId, setLoginId] = useState("");
  const [stage, setStage] = useState("");   // "" | "code" | "password"
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [wait, setWait] = useState(0);
  useEffect(() => { if (wait <= 0) return undefined; const t = setTimeout(() => setWait(wait - 1), 1000); return () => clearTimeout(t); }, [wait]);

  const sendCode = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    setMessage(""); setError("");
    if (!loginId.trim()) return setError("Enter your email or roll number.");
    setBusy(true);
    try {
      await api.post("/auth/forgot-password/", { login_id: loginId.trim() }, { skipAuth: true });
      setWait(30); setStage("code");
    } catch (err) {
      const { message: m, fields } = parseError(err);
      setError((fields && fields.login_id) || ""); setMessage(m);
    } finally { setBusy(false); }
  };

  return (
    <AuthFrame h="Forgot password">
      {message && <div className="alert alert-danger" role="alert">{message}</div>}
      <form onSubmit={sendCode} noValidate>
        <p className="gh-sub">Enter your email. We will send a 6-digit code to it.</p>
        <Field label="Email or Roll number" name="login_id" value={loginId} onChange={(e) => setLoginId(e.target.value)} error={error} autoFocus />
        <button className="gh-btn gh-btn-coral w-100 mt-3" disabled={busy}>{busy ? "Sending..." : "Send reset code"}</button>
        <p className="gh-hint mt-3">Not getting the email? Ask your admin to reset your password.</p>
      </form>
      <p className="gh-alt"><Link to="/login">Back to login</Link></p>
      {stage === "code" && (
        <CodeDialog loginId={loginId.trim()} wait={wait} onClose={() => setStage("")} onResend={sendCode}
          onVerified={(t) => { setToken(t); setStage("password"); }} />
      )}
      {stage === "password" && (
        <PasswordDialog token={token} onClose={() => setStage("")}
          onDone={() => navigate("/login", { replace: true, state: { reset: true } })} />
      )}
    </AuthFrame>
  );
}
