import axios from "axios";
import { handleApiError, isRetryableError, retryWithBackoff } from "../utils/errorHandler";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
});

// Ensure a token is always available after restarts (dev-friendly)
const DEV_JWT = import.meta.env.VITE_DEV_JWT as string | undefined;
const DEV_EMAIL = import.meta.env.VITE_DEV_EMAIL as string | undefined;
const DEV_PASSWORD = import.meta.env.VITE_DEV_PASSWORD as string | undefined;

// Bootstrap: if we have a dev JWT, persist it
if (DEV_JWT && !localStorage.getItem("jwt")) {
  try {
    localStorage.setItem("jwt", DEV_JWT);
  } catch {}
  api.defaults.headers.common["Authorization"] = `Bearer ${DEV_JWT}`;
}

// Opportunistic auto-login (runs on first request if no token)
let loginPromise: Promise<string | undefined> | null = null;

// Check if JWT token is expired
function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const now = Math.floor(Date.now() / 1000);
    return payload.exp < now;
  } catch {
    return true; // If we can't parse, consider it expired
  }
}

async function ensureToken(forceLogin = false): Promise<string | undefined> {
  const existing = (localStorage.getItem("jwt") ?? undefined) || (forceLogin ? undefined : DEV_JWT);
  
  // Check if existing token is expired
  if (existing && !isTokenExpired(existing) && !forceLogin) {
    return existing as string;
  }

  // Prefer env creds, else fall back to known dev creds provided by the user
  const email = DEV_EMAIL || import.meta.env.VITE_DEFAULT_ADMIN_EMAIL || "admin@example.com";
  const password = DEV_PASSWORD || import.meta.env.VITE_DEFAULT_ADMIN_PASSWORD || "admin123";

  // Use a bare client without interceptors to avoid recursion
  const bootstrap = axios.create({ baseURL: api.defaults.baseURL });
  try {
    const res = await bootstrap.post("/auth/login", { email, password });
    const token: string | undefined = res?.data?.access_token as string | undefined;
    if (token) {
      try { localStorage.setItem("jwt", token); } catch {}
      return token;
    }
  } catch (e) {
    // swallow; caller can proceed without token
    // console.warn("Auto-login failed", e);
  }
  return undefined;
}

// JWT interceptor for all requests
api.interceptors.request.use(async (config) => {
  // Reuse in-flight login to prevent parallel logins
  const tokenInStorage = (localStorage.getItem("jwt") ?? undefined) || DEV_JWT;
  let token: string | undefined = tokenInStorage;
  
  // Check if token is expired and get a new one if needed
  if (!token || isTokenExpired(token)) {
    loginPromise = loginPromise || ensureToken();
    token = await loginPromise;
    loginPromise = null;
  }
  
  if (token) {
    (config.headers as Record<string, string>).Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const status = err?.response?.status;
    const original: any = err?.config || {};
    
    if (status === 401) {
      // clear invalid token and attempt a single silent re-login + retry
      try { localStorage.removeItem("jwt"); } catch {}
      if (!original._retry) {
        original._retry = true;
        const token = await ensureToken(true); // ignore DEV_JWT, perform real login
        if (token) {
          original.headers = original.headers || {};
          (original.headers as Record<string, string>).Authorization = `Bearer ${token}`;
          return api.request(original);
        }
      }
    }
    
    // Handle retryable errors
    if (isRetryableError(err) && !original._retry && original.method?.toLowerCase() === 'get') {
      original._retry = true;
      try {
        return await retryWithBackoff(() => api.request(original), 2, 1000);
      } catch (retryError) {
        // If retry fails, fall through to normal error handling
      }
    }
    
    // Log and handle the error
    const errorMessage = handleApiError(err, `API ${original.method?.toUpperCase()} ${original.url}`);
    console.error("API error:", errorMessage);
    
    return Promise.reject(err);
  }
);