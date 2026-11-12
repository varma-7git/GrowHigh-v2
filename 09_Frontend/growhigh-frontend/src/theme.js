import { useEffect, useState } from "react";

const KEY = "gh_theme";

/** "light" is the default. The choice is kept in this browser. */
export function getTheme() {
  try { const s = localStorage.getItem(KEY); if (s === "dark" || s === "light") return s; } catch (e) { /* private window */ }
  return "light";
}

export function applyTheme(t) {
  const r = document.documentElement;
  r.setAttribute("data-theme", t);
  r.setAttribute("data-bs-theme", t);   // Bootstrap 5.3 themes its own forms, tables and alerts from this
}

export function setTheme(t) {
  try { localStorage.setItem(KEY, t); } catch (e) { /* private window */ }
  applyTheme(t);
  window.dispatchEvent(new Event("gh-theme"));
}

applyTheme(getTheme());   // before the first paint, so the page never flashes the wrong colours

export function useTheme() {
  const [t, setT] = useState(getTheme);
  useEffect(() => {
    const on = () => setT(getTheme());
    window.addEventListener("gh-theme", on);
    return () => window.removeEventListener("gh-theme", on);
  }, []);
  return [t, () => setTheme(t === "dark" ? "light" : "dark")];
}
