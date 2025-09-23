import { api } from "./client";

export type ActionRequest = {
  account_id: number;
  profile_id: number;
  usernames: string[];
  count?: number; // only for like-recent
};

export type ActionResponse = {
  log_id: number;
  status: string;
};

export const followAction = async (payload: ActionRequest): Promise<ActionResponse> => {
  const response = await api.post("/actions/follow", payload);
  return response.data;
};

export const unfollowAction = async (payload: ActionRequest): Promise<ActionResponse> => {
  const response = await api.post("/actions/unfollow", payload);
  return response.data;
};

export const likeRecentAction = async (payload: ActionRequest): Promise<ActionResponse> => {
  const response = await api.post("/actions/like-recent", payload);
  return response.data;
};

// Get recent action logs
export const getRecentLogs = async (limit = 50) => {
  const response = await api.get("/logs", { params: { limit } });
  return response.data;
};
