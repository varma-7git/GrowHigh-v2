import { useEffect, useRef } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { linkLabels, routeTitle } from "./a11y";
import ProtectedRoute from "./components/ProtectedRoute";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import RegisterCompany from "./pages/RegisterCompany";
import RegisterFaculty from "./pages/RegisterFaculty";
import NotFound from "./pages/NotFound";
import AdminHome from "./admin/AdminHome";
import CompanyHome from "./pages/CompanyHome";
import StudentApp from "./ws/student/StudentApp";
import FacultyApp from "./ws/faculty/FacultyApp";

export default function App() {
  const { pathname } = useLocation();
  const first = useRef(true);
  useEffect(() => linkLabels(), []);
  useEffect(() => {
    document.title = routeTitle(pathname);
    if (first.current) { first.current = false; return; }
    const main = document.getElementById("main");   // move keyboard and screen reader focus to the new page
    if (main) main.focus({ preventScroll: true });
  }, [pathname]);
  return (
    <>
    <a className="gh-skip" href="#main" onClick={(e) => { const m = document.getElementById("main"); if (m) { e.preventDefault(); m.focus(); m.scrollIntoView(); } }}>Skip to main content</a>
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/register-faculty" element={<RegisterFaculty />} />
      <Route path="/register-company" element={<RegisterCompany />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/student/*" element={<ProtectedRoute role="STUDENT"><StudentApp /></ProtectedRoute>} />
      <Route path="/faculty/*" element={<ProtectedRoute role="FACULTY"><FacultyApp /></ProtectedRoute>} />
      <Route path="/admin/*" element={<ProtectedRoute role="ADMIN"><AdminHome /></ProtectedRoute>} />
      <Route path="/company" element={<ProtectedRoute role="COMPANY"><CompanyHome /></ProtectedRoute>} />
      <Route path="*" element={<NotFound />} />
    </Routes>
    </>
  );
}
