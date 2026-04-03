export type AuthInfo = {
  token: string;
  role: "admin" | "recruiter";
  email: string;
};

const TOKEN_KEY = "hireblind_token";
const ROLE_KEY = "hireblind_role";
const EMAIL_KEY = "hireblind_email";

export function setAuthInfo(info: AuthInfo) {
  localStorage.setItem(TOKEN_KEY, info.token);
  localStorage.setItem(ROLE_KEY, info.role);
  localStorage.setItem(EMAIL_KEY, info.email);
}

export function clearAuthInfo() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  localStorage.removeItem(EMAIL_KEY);
}

export function getAuthInfo(): AuthInfo | null {
  const token = localStorage.getItem(TOKEN_KEY);
  const role = localStorage.getItem(ROLE_KEY) as AuthInfo["role"] | null;
  const email = localStorage.getItem(EMAIL_KEY);
  if (!token || !role || !email) return null;
  return { token, role, email };
}

