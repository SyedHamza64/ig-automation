import { api } from "./client";

export const getHealth = async (): Promise<string> => {
  // try /health/live → then /health/db → else “down”
  try {
    const r = await api.get("/health/live");
    return normalize(r.data);
  } catch {
    try {
      const r2 = await api.get("/health/db");
      return normalize(r2.data);
    } catch {
      return "down";
    }
  }
};

function normalize(data: any): string {
  if (typeof data === "string") return data;
  if (data?.status) return String(data.status);
  if (data?.detail) return String(data.detail);
  return "ok";
}
