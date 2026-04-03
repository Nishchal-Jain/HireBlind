import React, { useMemo, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { logout } from "./services/auth";
import { getAuthInfo, type AuthInfo } from "./services/storage";
import LoginPage from "./pages/LoginPage";
import AdminDashboard from "./pages/AdminDashboard";
import RecruiterDashboard from "./pages/RecruiterDashboard";
import CompliancePanel from "./pages/CompliancePanel";

function RequireRole({ allowedRoles, children }: { allowedRoles: AuthInfo["role"][]; children: React.ReactNode }) {
  const auth = getAuthInfo();
  if (!auth) return <Navigate to="/login" replace />;
  if (!allowedRoles.includes(auth.role)) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function ShellHeader({ onLogout }: { onLogout: () => void }) {
  const auth = useMemo(() => getAuthInfo(), []);
  const location = useLocation();
  const activePath = location.pathname;

  const tabs = useMemo(() => {
    if (!auth) return [];
    if (auth.role === "admin") {
      return [
        { to: "/admin", label: "Admin" },
        { to: "/compliance", label: "Compliance" },
      ];
    }
    return [
      { to: "/recruiter", label: "Recruiter" },
      { to: "/compliance", label: "Compliance" },
    ];
  }, [auth]);

  return (
    <div className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-6">
          <div className="font-semibold text-slate-800">HireBlind</div>
          {tabs.length ? (
            <nav className="flex items-center gap-2">
              {tabs.map((t) => {
                const active = activePath === t.to;
                return (
                  <Link
                    key={t.to}
                    to={t.to}
                    className={[
                      "rounded-md px-3 py-2 text-sm",
                      active ? "bg-slate-800 text-white" : "text-slate-700 hover:bg-slate-100",
                    ].join(" ")}
                  >
                    {t.label}
                  </Link>
                );
              })}
            </nav>
          ) : null}
        </div>

        <div className="flex items-center gap-3">
          {auth ? (
            <>
              <div className="text-sm text-slate-600">
                {auth.email} ({auth.role})
              </div>
              <button
                className="rounded-md bg-slate-800 px-3 py-2 text-sm text-white hover:bg-slate-700"
                onClick={onLogout}
              >
                Logout
              </button>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const location = useLocation();
  const [tick, setTick] = useState(0);

  const auth = getAuthInfo();
  // Refresh header auth snapshot when login/logout happens.
  // (hackathon-friendly: we just bump a state value)
  React.useEffect(() => {
    setTick((x) => x + 1);
  }, [location.pathname]);

  const onLogout = () => {
    logout();
    window.location.href = "/login";
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <ShellHeader key={tick} onLogout={onLogout} />
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/admin"
          element={
            <RequireRole allowedRoles={["admin"]}>
              <AdminDashboard />
            </RequireRole>
          }
        />
        <Route
          path="/recruiter"
          element={
            <RequireRole allowedRoles={["recruiter"]}>
              <RecruiterDashboard />
            </RequireRole>
          }
        />
        <Route
          path="/compliance"
          element={
            <RequireRole allowedRoles={["admin", "recruiter"]}>
              <CompliancePanel />
            </RequireRole>
          }
        />
        <Route path="*" element={<Navigate to={auth ? (auth.role === "admin" ? "/admin" : "/recruiter") : "/login"} replace />} />
      </Routes>
    </div>
  );
}

