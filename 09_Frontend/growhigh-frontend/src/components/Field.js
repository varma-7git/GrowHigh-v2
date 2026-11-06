import { useState } from "react";

/** Label + input + error text. type="password" gets a Show/Hide toggle. */
export default function Field({ label, name, error, hint, type = "text", className = "", children, ...rest }) {
  const [show, setShow] = useState(false);
  const isPw = type === "password";
  const id = `f-${name}`;
  return (
    <div className={`gh-field ${className}`}>
      <label htmlFor={id}>{label}</label>
      <div className="gh-input-wrap">
        {children || (
          <input id={id} name={name} type={isPw && show ? "text" : type}
            className={`form-control ${error ? "is-invalid" : ""}`}
            aria-invalid={error ? "true" : undefined} aria-describedby={error ? `${id}-msg` : hint ? `${id}-msg` : undefined} {...rest} />
        )}
        {isPw && (
          <button type="button" className="gh-toggle" aria-pressed={show} aria-label={show ? `Hide ${label}` : `Show ${label}`} onClick={() => setShow(!show)}>
            {show ? "Hide" : "Show"}
          </button>
        )}
      </div>
      {error ? <div className="gh-error" id={`${id}-msg`} role="alert">{error}</div> : hint ? <div className="gh-hint" id={`${id}-msg`}>{hint}</div> : null}
    </div>
  );
}
