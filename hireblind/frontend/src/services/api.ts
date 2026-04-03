import axios from "axios";
import { clearAuthInfo, getAuthInfo } from "./storage";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use((config) => {
  const auth = getAuthInfo();
  if (auth?.token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${auth.token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err?.response?.status;
    const url = String(err?.config?.url ?? "");
    const onLoginOrSignup = url.includes("/auth/login") || url.includes("/auth/signup");
    if (status === 401 && !onLoginOrSignup && err?.config?.headers?.Authorization) {
      clearAuthInfo();
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.replace("/login?session=expired");
      }
    }
    const d = err?.response?.data?.detail;
    let msg: string | undefined;
    if (Array.isArray(d)) {
      msg = d
        .map((x: unknown) =>
          typeof x === "object" && x !== null && "msg" in x
            ? String((x as { msg?: string }).msg ?? x)
            : String(x),
        )
        .join("; ");
    } else if (typeof d === "string") {
      msg = d;
    } else if (d && typeof d === "object") {
      msg = JSON.stringify(d);
    }
    if (msg) {
      err.message = msg;
    }
    return Promise.reject(err);
  },
);

/** Normalise FastAPI / axios errors for UI strings. */
export function formatApiError(err: unknown): string {
  const e = err as { message?: string; response?: { data?: { detail?: unknown } } };
  if (typeof e?.message === "string" && e.message) return e.message;
  const detail = e?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((x: unknown) =>
        typeof x === "object" && x !== null && "msg" in x ? String((x as { msg?: string }).msg) : String(x),
      )
      .join("; ");
  }
  return "Request failed";
}

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
  role: "admin" | "recruiter";
  email: string;
};

