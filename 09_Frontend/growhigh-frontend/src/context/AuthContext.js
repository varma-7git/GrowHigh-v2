import { createContext, useCallback, useContext, useMemo, useState } from "react";
import api, { tokenStore } from "../api/client";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export const homeFor = (role) => ({ STUDENT: "/student", FACULTY: "/faculty", ADMIN: "/admin", COMPANY: "/company" }[role] || "/login");

const savedUser = () => tokenStore.user;

export function AuthProvider({ children }) {
  const [user, setUser] = useState(savedUser);

  const login = useCallback(async (loginId, password, remember = false) => {
    const { data } = await api.post("/auth/login/", { login_id: loginId, password }, { skipAuth: true });
    tokenStore.setRemember(remember);
    tokenStore.set(data.access, data.refresh);
    tokenStore.setUser(data.user);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      if (tokenStore.refresh) await api.post("/auth/logout/", { refresh: tokenStore.refresh });
    } catch { /* token may already be expired; still log out locally */ }
    tokenStore.clear();
    setUser(null);
  }, []);

  const update = useCallback((u) => { tokenStore.setUser(u); setUser(u); }, []);
  const value = useMemo(() => ({ user, login, logout, update }), [user, login, logout, update]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
