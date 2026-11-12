import { useCallback, useEffect, useState } from "react";
import api from "./api/client";

/** Notifications kept for each user on this device. Right now: the welcome note sent at the very first login. */
const key = (id) => `gh_notes_${id}`;

export function getNotes(userId) {
  try { return JSON.parse(localStorage.getItem(key(userId)) || "[]"); } catch { return []; }
}
function save(userId, list) { try { localStorage.setItem(key(userId), JSON.stringify(list.slice(0, 30))); } catch { /* storage blocked: skip */ } }

export function addNote(userId, note) {
  const list = getNotes(userId);
  if (list.some((n) => n.id === note.id)) return;
  save(userId, [{ ...note, read: false, at: new Date().toISOString() }, ...list]);
}
export function markOneRead(userId, id) {
  if (String(id).startsWith("n")) { api.post("/notices/read/", { id: Number(String(id).slice(1)) }).catch(() => {}); return; }
  save(userId, getNotes(userId).map((n) => (n.id === id ? { ...n, read: true } : n)));
}
export function markAllRead(userId) {
  save(userId, getNotes(userId).map((n) => ({ ...n, read: true })));
  api.post("/notices/read/").catch(() => {});
}

/** Notes kept on this device plus notices from the server (new lessons, feedback). Refreshes every minute. */
export function useNoteList(userId, all = false) {
  const [list, setList] = useState(() => getNotes(userId));
  const refresh = useCallback(() => {
    const local = getNotes(userId);
    api.get("/notices/", { params: all ? { all: 1 } : {} }).then((r) => {
      const server = (r.data || []).map((n) => ({ id: `n${n.id}`, title: n.title, text: n.text, link: n.link, read: n.read, at: n.at }));
      setList([...server, ...local].sort((a, b) => String(b.at).localeCompare(String(a.at))));
    }).catch(() => setList(local));
  }, [userId, all]);
  useEffect(() => { refresh(); const t = setInterval(refresh, 60000); return () => clearInterval(t); }, [refresh]);
  return [list, refresh];
}
export const unreadCount = (userId) => getNotes(userId).filter((n) => !n.read).length;

const WELCOME = {
  STUDENT: "Your account is ready. Start with ECET preparation, take a daily test and watch your results grow.",
  FACULTY: "Your account is ready. Add study material and questions, then create tests for your students.",
  ADMIN: "Your account is ready. Set up branches, subjects and topics, then review new requests.",
  COMPANY: "Your account is ready. Post jobs and internships for students to see.",
};
export function addWelcome(user) {
  addNote(user.id, { id: "welcome", title: `Welcome to GrowHigh, ${(user.full_name || "").split(" ")[0] || "there"}!`, text: WELCOME[user.role] || WELCOME.STUDENT });
}
