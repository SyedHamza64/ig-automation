import { api } from "../api/client";

export type ProfileRow = {
  id: number;
  account_id: number | null;
  account_handle: string | null;
  adspower_profile_id: string;
  health: string | null;
  last_ws_puppeteer: string | null;
  last_opened_at?: string | null; // if backend later returns it
};

export type LoginState = "logged_in" | "login" | "error" | "unknown";

export const listProfiles = async (): Promise<ProfileRow[]> =>
  (await api.get("/profiles")).data;

export const openProfile = async (id: number | string) => 
  (await api.post(`/profiles/${id}/open`)).data;

export const closeProfile = async (id: number | string) => 
  (await api.post(`/profiles/${id}/close`)).data;

export const wsCheck = async (id: number | string) => 
  (await api.get(`/profiles/${id}/ws-check`)).data;

export const probeProfile = async (id: number | string) => 
  (await api.get(`/profiles/${id}/probe`)).data;

export const getLoginState = async (profile_id: number | string): Promise<{ state: LoginState }> => {
  const response = (await api.get(`/engine/login-state`, { params: { profile_id } })).data;
  return { state: response.login?.state || "unknown" };
};

// Warmup stream for a profile (SSE via token in query)
export const startWarmupStream = (profile_id: number | string, content: "home"|"reels" = "reels", durationSec = 0, maxLikes = -1): EventSource => {
  const base = api.defaults.baseURL || "";
  const token = localStorage.getItem("jwt") || "";
  const qs = new URLSearchParams({
    account_id: String(0),
    profile_id: String(profile_id),
    duration_sec: String(durationSec),
    max_likes: String(maxLikes),
    content,
    token,
  }).toString();
  const url = `${base}/actions/warmup-stream-open?${qs}`;
  return new EventSource(url);
};
