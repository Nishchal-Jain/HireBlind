import { api, type LoginResponse } from "./api";
import { setAuthInfo, clearAuthInfo, type AuthInfo } from "./storage";

export async function login(email: string, password: string): Promise<AuthInfo> {
  const res = await api.post<LoginResponse>("/auth/login", { email, password });
  const data = res.data;
  const info: AuthInfo = {
    token: data.access_token,
    role: data.role,
    email: data.email,
  };
  setAuthInfo(info);
  return info;
}

export async function signup(email: string, password: string, role: AuthInfo["role"]): Promise<void> {
  await api.post("/auth/signup", { email, password, role });
}

export function logout() {
  clearAuthInfo();
}

