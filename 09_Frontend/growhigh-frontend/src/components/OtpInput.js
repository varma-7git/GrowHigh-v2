import { useEffect, useRef } from "react";

/** Six separate boxes for a one-time code. Digits only. Typing moves to the next box, Backspace to the previous one,
 *  arrow keys move around, and pasting a full code fills every box. `onChange` gets the code as a string. */
export default function OtpInput({ value, onChange, length = 6, autoFocus = false, disabled = false, onComplete, label = "Verification code" }) {
  const refs = useRef([]);
  const digits = Array.from({ length }, (_, i) => value[i] || "");

  useEffect(() => { if (autoFocus && refs.current[0]) refs.current[0].focus(); }, [autoFocus]);

  const focus = (i) => { const el = refs.current[Math.max(0, Math.min(length - 1, i))]; if (el) { el.focus(); el.select(); } };
  const commit = (next) => { onChange(next); if (next.length === length && onComplete) onComplete(next); };

  const type = (i, raw) => {
    const clean = raw.replace(/\D/g, "");
    if (!clean) return;
    const arr = digits.slice();
    if (clean.length === 1) { arr[i] = clean; commit(arr.join("").slice(0, length)); focus(i + 1); return; }
    // several digits at once (autofill or paste into one box)
    clean.slice(0, length - i).split("").forEach((d, k) => { arr[i + k] = d; });
    commit(arr.join("").slice(0, length));
    focus(i + clean.length);
  };

  const key = (i, e) => {
    if (e.key === "Backspace") {
      e.preventDefault();
      const arr = digits.slice();
      if (arr[i]) { arr[i] = ""; onChange(arr.join("")); } else if (i > 0) { arr[i - 1] = ""; onChange(arr.join("")); focus(i - 1); }
    } else if (e.key === "ArrowLeft") { e.preventDefault(); focus(i - 1); }
    else if (e.key === "ArrowRight") { e.preventDefault(); focus(i + 1); }
  };

  const paste = (e) => {
    const text = (e.clipboardData.getData("text") || "").replace(/\D/g, "").slice(0, length);
    if (!text) return;
    e.preventDefault();
    commit(text);
    focus(text.length >= length ? length - 1 : text.length);
  };

  return (
    <div className="gh-otp" role="group" aria-label={label} onPaste={paste}>
      {digits.map((d, i) => (
        <input key={i} ref={(el) => { refs.current[i] = el; }} className={`gh-otp-box${d ? " filled" : ""}`}
          type="text" inputMode="numeric" pattern="[0-9]*" autoComplete={i === 0 ? "one-time-code" : "off"} maxLength={length}
          value={d} disabled={disabled} aria-label={`${label}, digit ${i + 1} of ${length}`}
          onChange={(e) => type(i, e.target.value)} onKeyDown={(e) => key(i, e)} onFocus={(e) => e.target.select()} />
      ))}
    </div>
  );
}
