import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
});

// Optional: DEV token to skip FE login in development
const DEV_JWT = import.meta.env.VITE_DEV_JWT;
if (DEV_JWT) {
  api.defaults.headers.common["Authorization"] = `Bearer ${DEV_JWT}`;
}

api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error("API error:", err?.response?.status, err?.response?.data);
    return Promise.reject(err);
  }
);