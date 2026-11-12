import { useState } from "react";
import { useNavigate } from "react-router-dom";
import WsShell from "./Shell";
import { Stats } from "./kit";
import { AdminShell } from "../admin/ui";
import { useAuth } from "../context/AuthContext";
import { markAllRead, markOneRead, useNoteList } from "../notes";

const KINDS = {
  lesson: { label: "New lesson", icon: "M2 4h7a3 3 0 013 3v13a2 2 0 00-2-2H2zM22 4h-7a3 3 0 00-3 3v13a2 2 0 012-2h8z", bg: "var(--tint-blue, #e6f4ff)", fg: "var(--tint-blue-fg, #0b5c99)" },
  feedback: { label: "Feedback", icon: "M21 12a8 8 0 01-11.6 7.1L4 20l1-4.6A8 8 0 1121 12z", bg: "var(--tint-green, #dff6ea)", fg: "var(--tint-green-fg, #14703d)" },
  reminder: { label: "Reminder", icon: "M12 7v5l3 2M21 12a9 9 0 11-18 0 9 9 0 0118 0z", bg: "var(--tint-amber, #fff1d6)", fg: "var(--tint-amber-fg, #8a5a00)" },
  general: { label: "General", icon: "M6 8a6 6 0 1112 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.9 1.9 0 003.4 0", bg: "var(--tint-grey, #eef2f7)", fg: "var(--mu2, #55667c)" },
};
const kindOf = (n) => (/^New lesson/.test(n.title) ? "lesson" : /^Feedback/.test(n.title) ? "feedback" : /^Lessons waiting/.test(n.title) ? "reminder" : "general");

const dayStart = (d) => { const x = new Date(d); x.setHours(0, 0, 0, 0); return x.getTime(); };
const DAY = 86400000;
const bucket = (at) => {
  const diff = Math.round((dayStart(new Date()) - dayStart(at)) / DAY);
  return diff <= 0 ? "Today" : diff === 1 ? "Yesterday" : diff < 7 ? "This week" : "Earlier";
};
const ORDER = ["Today", "Yesterday", "This week", "Earlier"];
const when = (at) => {
  const d = new Date(at);
  const t = d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  const diff = Math.round((dayStart(new Date()) - dayStart(d)) / DAY);
  return diff <= 0 ? t : diff === 1 ? `Yesterday, ${t}` : d.toLocaleDateString("en-GB", { day: "2-digit", month: "short" }) + `, ${t}`;
};

function Body({ role }) {
  const { user } = useAuth();
  const nav = useNavigate();
  const [list, refresh] = useNoteList(user.id, true);
  const [show, setShow] = useState("all");
  const unread = list.filter((n) => !n.read).length;
  const count = (k) => list.filter((n) => kindOf(n) === k).length;
  const shown = list.filter((n) => (show === "all" ? true : show === "unread" ? !n.read : kindOf(n) === show));
  const groups = ORDER.map((g) => [g, shown.filter((n) => bucket(n.at) === g)]).filter(([, l]) => l.length);
  const open = (n) => { if (!n.read) { markOneRead(user.id, n.id); setTimeout(refresh, 300); } if (n.link) nav(n.link); };
  const allRead = () => { markAllRead(user.id); setTimeout(refresh, 300); };
  const btn = (on) => `ad-btn ${on ? "c" : "o"} s`;
  const tabs = [["all", `All (${list.length})`], ["unread", `Unread (${unread})`], ["lesson", `New lessons (${count("lesson")})`], ["feedback", `Feedback (${count("feedback")})`], ["reminder", `Reminders (${count("reminder")})`]];
  return (<>
    <Stats items={[["Notifications", String(list.length), "All received"], ["Unread", String(unread), unread ? "Waiting for you" : "All caught up"], ["New lessons", String(count("lesson")), "Posted for you"]]} />
    <div className="ad-card" style={{ marginBottom: 22 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <div className="ws-btns" style={{ margin: 0 }}>{tabs.map(([k, l]) => <button key={k} type="button" className={btn(show === k)} onClick={() => setShow(k)}>{l}</button>)}</div>
        <button type="button" className="ad-btn o s" disabled={!unread} onClick={allRead}>Mark all as read</button>
      </div>
    </div>
    {shown.length === 0 && <div className="ad-empty">{list.length === 0 ? "No notifications yet. New lessons and feedback will appear here." : "Nothing here. Try another filter."}</div>}
    {groups.map(([g, items]) => (
      <div key={g} style={{ marginBottom: 26 }}>
        <div className="ad-eyebrow" style={{ margin: "0 0 10px" }}>{g}</div>
        <div className="ad-card" style={{ padding: "6px 24px" }}>
          {items.map((n, i) => {
            const k = KINDS[kindOf(n)];
            return (
              <div key={n.id} onClick={() => open(n)} role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(n); } }}
                style={{ display: "flex", gap: 16, alignItems: "flex-start", padding: "18px 0", borderTop: i ? "1px solid var(--ln, #e6ecf4)" : 0, cursor: n.link ? "pointer" : "default" }}>
                <span aria-hidden="true" style={{ width: 44, height: 44, borderRadius: "50%", background: k.bg, color: k.fg, display: "grid", placeItems: "center", flex: "none" }}>
                  <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d={k.icon} /></svg></span>
                <span style={{ flex: 1, minWidth: 0 }}>
                  <span style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                    <b style={{ fontWeight: n.read ? 600 : 800 }}>{n.title}</b>
                    <span className="ad-pill" style={{ margin: 0, background: k.bg, color: k.fg }}>{k.label}</span>
                    {!n.read && <span className="ad-pill warn" style={{ margin: 0 }}>New</span>}</span>
                  <span style={{ display: "block", color: "var(--mu2, #55667c)", margin: "4px 0 2px", overflowWrap: "anywhere" }}>{n.text}</span>
                  <small style={{ color: "var(--mu, #6b7a90)" }}>{when(n.at)}{n.link ? " · Click to open" : ""}</small></span>
              </div>);
          })}
        </div>
      </div>))}
  </>);
}

export default function Notifications({ role }) {
  if (role === "admin") return <AdminShell crumb="Notifications" title="Notifications" subtitle="Everything sent to you, newest first."><Body role={role} /></AdminShell>;
  return <WsShell role={role} crumb="Notifications" title="Notifications" subtitle="Everything sent to you, newest first."><Body role={role} /></WsShell>;
}
