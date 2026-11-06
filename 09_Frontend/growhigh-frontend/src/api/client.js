import axios from "axios";

export const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000/api/v1";

// "Keep me signed in" = tokens live in localStorage (survive closing the browser).
// Otherwise they live in sessionStorage and the login ends when the browser window is closed.
const remembered = () => { try { return localStorage.getItem("gh_remember") === "1"; } catch (e) { return false; } };
const area = () => { try { return remembered() ? localStorage : sessionStorage; } catch (e) { return null; } };
const read = (k) => { try { const a = area(); return a ? a.getItem(k) : null; } catch (e) { return null; } };
const write = (k, v) => { try { const a = area(); if (a) a.setItem(k, v); } catch (e) { /* storage blocked */ } };

// Older versions kept the login in localStorage for everyone. Drop it unless "Keep me signed in" was chosen.
(function dropLegacy() { // legacy
  try {
    if (localStorage.getItem("gh_remember") !== "1") ["gh_access", "gh_refresh", "gh_user"].forEach((k) => localStorage.removeItem(k));
  } catch (e) { /* storage blocked */ }
})();

const store = {
  get access() { return read("gh_access"); },
  get refresh() { return read("gh_refresh"); },
  set(access, refresh) {
    if (access) write("gh_access", access);
    if (refresh) write("gh_refresh", refresh);
  },
  get user() { try { return JSON.parse(read("gh_user")); } catch (e) { return null; } },
  setUser(u) { write("gh_user", JSON.stringify(u)); },
  setRemember(on) {
    try {
      this.clear();
      if (on) localStorage.setItem("gh_remember", "1"); else localStorage.removeItem("gh_remember");
    } catch (e) { /* storage blocked */ }
  },
  clear() {
    ["gh_access", "gh_refresh", "gh_user"].forEach((k) => {
      try { localStorage.removeItem(k); sessionStorage.removeItem(k); } catch (e) { /* ignore */ }
    });
  },
};
export const tokenStore = store;

const api = axios.create({ baseURL: API_URL, headers: { "Content-Type": "application/json" } });

api.interceptors.request.use((config) => {
  if (store.access && !config.skipAuth) config.headers.Authorization = `Bearer ${store.access}`;
  return config;
});

// One silent refresh when the access token has expired, then retry the request once.
let refreshing = null;
api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry && !original.skipAuth && store.refresh) {
      original._retry = true;
      try {
        refreshing = refreshing || axios.post(`${API_URL}/auth/refresh/`, { refresh: store.refresh });
        const { data } = await refreshing;
        refreshing = null;
        store.set(data.access, data.refresh);
        original.headers.Authorization = `Bearer ${data.access}`;
        return api(original);
      } catch (e) {
        refreshing = null;
        store.clear();
        window.location.assign("/login");
      }
    }
    return Promise.reject(error);
  }
);

/** Turns a backend error {detail, errors:{field:[msg]}} into { message, fields }. */
export function parseError(error) {
  const res = error.response;
  if (!res) return { message: "Cannot reach the server. Is the backend running?", fields: {} };
  const data = res.data || {};
  const fields = {};
  const source = data.errors || (typeof data === "object" && !data.detail ? data : {});
  Object.entries(source).forEach(([k, v]) => {
    fields[k] = Array.isArray(v) ? v.join(" ") : String(v);
  });
  let message = data.detail || "";
  if (res.status === 429) message = "Too many attempts. Please wait a little and try again.";
  if (!message && Object.keys(fields).length) message = "Please fix the highlighted fields.";
  return { message: message || "Something went wrong. Please try again.", fields };
}

export default api;
