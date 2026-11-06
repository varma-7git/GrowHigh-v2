/** Accessibility helpers that apply to the whole app.
 *  - linkLabels(): a <label> placed next to a field without htmlFor is connected to it, and fields with no
 *    label at all (search boxes, icon buttons) get an accessible name from their placeholder or title.
 *  - routeTitle(): the browser tab title for each page, read out by screen readers on navigation. */
let n = 0;
const CONTROLS = "input:not([type=hidden]),select,textarea";

function nextControl(label) {
  let el = label.nextElementSibling;
  for (let i = 0; el && i < 3; i += 1, el = el.nextElementSibling) {
    if (el.matches(CONTROLS)) return el;
    const inner = el.querySelector && el.querySelector(CONTROLS);
    if (inner && el.tagName !== "LABEL") return inner;
    if (el.tagName === "LABEL") return null; // the next label belongs to the next field
  }
  return null;
}

function fix(root) {
  root.querySelectorAll("label:not([for])").forEach((label) => {
    if (label.querySelector(CONTROLS)) return;            // field is inside the label already
    const c = nextControl(label);
    if (!c) return;
    if (!c.id) { n += 1; c.id = `gh-auto-${n}`; }
    label.setAttribute("for", c.id);
  });
  root.querySelectorAll(CONTROLS).forEach((c) => {
    if (c.getAttribute("aria-label") || c.getAttribute("aria-labelledby") || c.closest("label")) return;
    if (c.id && root.querySelector(`label[for="${CSS.escape(c.id)}"]`)) return;
    const name = c.getAttribute("placeholder") || c.getAttribute("title");
    if (name) c.setAttribute("aria-label", name);
  });
  root.querySelectorAll("button:not([aria-label])").forEach((b) => {
    if (!b.textContent.trim() && b.getAttribute("title")) b.setAttribute("aria-label", b.getAttribute("title"));
  });
}

export function linkLabels() {
  if (typeof document === "undefined" || typeof MutationObserver === "undefined") return () => {};
  let queued = false;
  const run = () => { queued = false; try { fix(document.body); } catch (e) { /* never break the page */ } };
  const obs = new MutationObserver(() => { if (!queued) { queued = true; requestAnimationFrame(run); } });
  obs.observe(document.body, { childList: true, subtree: true });
  run();
  return () => obs.disconnect();
}

const TITLES = [
  ["/login", "Login"], ["/register-faculty", "Faculty registration"], ["/register-company", "Company registration"],
  ["/register", "Student registration"], ["/forgot-password", "Reset password"],
  ["/student", "Student workspace"], ["/faculty", "Faculty workspace"], ["/admin", "Admin workspace"], ["/company", "Company"],
];
export function routeTitle(pathname) {
  const hit = TITLES.find(([p]) => pathname === p || pathname.startsWith(`${p}/`));
  if (hit) return `${hit[1]} · GrowHigh`;
  return pathname === "/" ? "GrowHigh · Learn. Prepare. Grow." : "Page not found · GrowHigh";
}
