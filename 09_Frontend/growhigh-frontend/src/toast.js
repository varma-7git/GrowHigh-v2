/** Small message that appears for a few seconds, then goes away. Works across page changes. */
export function showToast(text, kind = "success") {
  const old = document.getElementById("gh-toast");
  if (old) old.remove();
  const el = document.createElement("div");
  el.id = "gh-toast";
  el.setAttribute("role", "status");
  el.setAttribute("aria-live", "polite");
  el.textContent = text;
  el.style.cssText = "position:fixed;top:18px;left:50%;transform:translate(-50%,-12px);z-index:3000;padding:13px 22px;border-radius:14px;"
    + "font:700 15px 'Plus Jakarta Sans',system-ui,sans-serif;color:#fff;box-shadow:0 14px 34px rgba(6,26,46,.28);opacity:0;"
    + "transition:opacity .25s,transform .25s;max-width:92vw;text-align:center;background:" + (kind === "success" ? "#0b8f63" : "#b42b1d");
  document.body.appendChild(el);
  requestAnimationFrame(() => { el.style.opacity = "1"; el.style.transform = "translate(-50%,0)"; });
  setTimeout(() => { el.style.opacity = "0"; setTimeout(() => el.remove(), 300); }, 3000);
}

/** Ask before logging out, in a styled popup (not the browser's alert box). Resolves true or false. */
export function confirmLogout() {
  return new Promise((resolve) => {
    const before = document.activeElement;
    const wrap = document.createElement("div");
    wrap.setAttribute("role", "alertdialog"); wrap.setAttribute("aria-modal", "true"); wrap.setAttribute("aria-labelledby", "gh-cf-t");
    wrap.style.cssText = "position:fixed;inset:0;z-index:3100;background:rgba(6,26,46,.6);display:flex;align-items:center;justify-content:center;padding:16px;font-family:'Plus Jakarta Sans',system-ui,sans-serif";
    const box = document.createElement("div");
    box.style.cssText = "background:var(--surface,#fff);border-radius:22px;padding:28px 26px 22px;max-width:380px;width:100%;box-shadow:0 24px 60px rgba(6,26,46,.35);text-align:center";
    box.innerHTML = '<h3 id="gh-cf-t" style="margin:0 0 8px;font-size:20px;color:var(--tx,#0b1f33)">Logout?</h3>'
      + '<p style="margin:0 0 22px;color:var(--mu2,#56667f);font-size:15px">Are you sure you want to logout?</p>';
    const row = document.createElement("div");
    row.style.cssText = "display:flex;gap:10px;justify-content:center";
    const mk = (label, bg, fg, border) => { const b = document.createElement("button"); b.type = "button"; b.textContent = label;
      b.style.cssText = `padding:11px 24px;border-radius:12px;border:${border};background:${bg};color:${fg};font:700 15px inherit;cursor:pointer`; return b; };
    const no = mk("Cancel", "var(--surface,#fff)", "var(--tx,#0b1f33)", "1px solid var(--ln,#d5deea)");
    const yes = mk("Logout", "#ff6b5b", "#0b1f33", "0");
    row.append(no, yes); box.appendChild(row); wrap.appendChild(box); document.body.appendChild(wrap);
    const done = (v) => { document.removeEventListener("keydown", key); wrap.remove(); if (before && before.focus) before.focus(); resolve(v); };
    const key = (e) => {
      if (e.key === "Escape") done(false);
      if (e.key === "Tab") { e.preventDefault(); (document.activeElement === yes ? no : yes).focus(); }
    };
    document.addEventListener("keydown", key);
    no.onclick = () => done(false); yes.onclick = () => done(true);
    wrap.addEventListener("mousedown", (e) => { if (e.target === wrap) done(false); });
    yes.focus();
  });
}
