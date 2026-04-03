import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, signup } from "../services/auth";
import type { AuthInfo } from "../services/storage";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<AuthInfo["role"]>("recruiter");
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "login") {
        const info = await login(email.trim(), password);
        navigate(info.role === "admin" ? "/admin" : "/recruiter");
      } else {
        await signup(email.trim(), password, role);
        setMode("login");
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? err?.message ?? "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md p-6">
      <div className="mb-6">
        <div className="text-2xl font-semibold text-slate-800">HireBlind</div>
        <div className="mt-1 text-sm text-slate-600">Bias-free resume screening</div>
      </div>

      <form onSubmit={onSubmit} className="rounded-lg bg-white p-5 shadow-sm border border-slate-200">
        <div className="mb-4 flex gap-3">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={mode === "login" ? "font-semibold text-slate-900" : "text-slate-600"}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setMode("signup")}
            className={mode === "signup" ? "font-semibold text-slate-900" : "text-slate-600"}
          >
            Sign up
          </button>
        </div>

        <label className="block text-sm font-medium text-slate-800 mb-1">Email</label>
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          type="email"
          required
          className="w-full rounded-md border border-slate-300 px-3 py-2 mb-3"
          placeholder="you@example.com"
        />

        <label className="block text-sm font-medium text-slate-800 mb-1">Password</label>
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          type="password"
          required
          className="w-full rounded-md border border-slate-300 px-3 py-2 mb-3"
          placeholder="••••••••"
        />

        {mode === "signup" ? (
          <>
            <label className="block text-sm font-medium text-slate-800 mb-1">Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as AuthInfo["role"])}
              className="w-full rounded-md border border-slate-300 px-3 py-2 mb-4"
            >
              <option value="admin">admin</option>
              <option value="recruiter">recruiter</option>
            </select>
          </>
        ) : null}

        {error ? <div className="mb-3 text-sm text-red-600">{error}</div> : null}

        <button
          disabled={loading}
          type="submit"
          className="w-full rounded-md bg-slate-800 px-4 py-2 text-white font-medium hover:bg-slate-700 disabled:opacity-60"
        >
          {loading ? "Working..." : mode === "login" ? "Login" : "Create account"}
        </button>

        <div className="mt-4 text-xs text-slate-600">
          Demo users: <code>admin@example.com</code> / <code>Admin123!</code> and <code>recruiter@example.com</code> /
          <code>Recruit123!</code>
        </div>
      </form>
    </div>
  );
}

