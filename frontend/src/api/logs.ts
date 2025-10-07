import { api } from "./client";

export type ActionLog = {
    id: number;
    account_id: number;
    profile_id: number;
    action: string;
    status: string;
    error_message?: string | null;
    created_at: string;
    result?: any;
    payload?: any;
    mode?: string | null;
  };
  
export const listRecentLogs = async (limit = 20): Promise<ActionLog[]> => {
  const r = await api.get("/logs", { params: { limit } });
  // Handle the API response structure: array directly or { value: [...], Count: ... }
  return Array.isArray(r.data) ? r.data : (r.data.value || r.data) as ActionLog[];
};

