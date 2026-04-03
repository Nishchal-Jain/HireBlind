import axios from "axios";
import { getAuthInfo } from "./storage";

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

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
  role: "admin" | "recruiter";
  email: string;
};

