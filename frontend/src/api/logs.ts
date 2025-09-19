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
  };
  
export const listRecentLogs = async (limit = 20): Promise<ActionLog[]> => {
  const r = await api.get("/logs", { params: { limit } });
  return r.data as ActionLog[];
};

