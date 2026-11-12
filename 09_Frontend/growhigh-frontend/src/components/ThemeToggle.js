import { useTheme } from "../theme";

const SUN = "M12 4V2M12 22v-2M4 12H2M22 12h-2M5.6 5.6 4.2 4.2M19.8 19.8l-1.4-1.4M5.6 18.4l-1.4 1.4M19.8 4.2l-1.4 1.4M12 17a5 5 0 100-10 5 5 0 000 10z";
const MOON = "M21 13.2A8.5 8.5 0 1110.8 3a7 7 0 0010.2 10.2z";

/** Light / dark switch. In a header it looks like the bell button; floating, it sits in the corner of public pages. */
export default function ThemeToggle({ floating = false }) {
  const [t, toggle] = useTheme();
  const dark = t === "dark";
  const label = dark ? "Switch to light mode" : "Switch to dark mode";
  return (
    <button type="button" className={floating ? "gh-theme-float" : "ad-bell gh-theme"} onClick={toggle} aria-label={label} title={label} aria-pressed={dark}>
      <svg viewBox="0 0 24 24" aria-hidden="true" style={{ width: 22, height: 22, stroke: "currentColor", fill: "none", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" }}><path d={dark ? SUN : MOON} /></svg>
    </button>
  );
}
