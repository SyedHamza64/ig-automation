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

// Start mass follow stream (SSE) with section filter (followers | following)
export type MassFollowParams = {
  account_id: number;
  profile_id: number;
  username: string;
  limit?: number;
  section?: "followers" | "following";
};

export const startMassFollowStream = ({ account_id, profile_id, username, limit = 10, section = "followers" }: MassFollowParams): EventSource => {
  const base = api.defaults.baseURL || "";
  const token = localStorage.getItem("jwt") || "";
  const qs = new URLSearchParams({
    account_id: String(account_id),
    profile_id: String(profile_id),
    username,
    mode: "follow",
    limit: String(limit),
    section,
    token,
  }).toString();
  const url = `${base}/actions/mass-follow-stream-open?${qs}`;
  return new EventSource(url);
};
