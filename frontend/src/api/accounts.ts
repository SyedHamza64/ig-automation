import { api } from "./client";

export type AccountRow = { 
  id: number; 
  handle: string; 
  profile_id: number | null; 
  adspower_profile_id?: string | null 
};

export type LoginState = "logged_in" | "login" | "error" | "unknown";

export const listAccounts = async (): Promise<AccountRow[]> => {
  console.log("[listAccounts] Making API call to /accounts");
  try {
    const response = await api.get("/accounts");
    console.log("[listAccounts] Response:", response.data);
    return response.data;
  } catch (error) {
    console.error("[listAccounts] Error:", error);
    throw error;
  }
};

export const getAccountStats = async (id: number, days = 30) => 
  (await api.get(`/accounts/${id}/stats`, { params: { days } })).data;

export const getRecentActions = async (id: number, limit = 50) => 
  (await api.get(`/accounts/${id}/recent-actions`, { params: { limit } })).data;

export const getAccountLimits = async (id: number) => 
  (await api.get(`/accounts/${id}/limits`)).data;

export const getLoginState = async (profile_id: number) => {
  const response = (await api.get(`/engine/login-state`, { params: { profile_id } })).data;
  return { state: response.login?.state || "unknown" };
};

export const wsCheckProfile = async (profile_id: number) => 
  (await api.get(`/profiles/${profile_id}/ws-check`)).data;

// Legacy functions (keep for compatibility)
export const createAccount = async (body: { username: string; profile_id?: number | string }) =>
  (await api.post("/accounts", body)).data;

export const deleteAccount = async (id: number) =>
  (await api.delete(`/accounts/${id}`)).data;
