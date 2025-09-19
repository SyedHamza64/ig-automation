import { api } from "../api/client";

export const openProfile = async (profile_db_id: number | string) =>
  (await api.post(`/profiles/${profile_db_id}/open`)).data;

export type LoginState = "logged_in" | "login" | "error" | "unknown";

export const getLoginState = async (profile_id: number | string): Promise<{ state: LoginState }> =>
  (await api.get(`/engine/login-state`, { params: { profile_id } })).data;

// optional helpers if you want buttons later:
export const attachProfile = async (payload: { profile_id: number | string }) =>
  (await api.post(`/profiles/attach`, payload)).data;

export const closeProfile = async (profile_db_id: number | string) =>
  (await api.post(`/profiles/${profile_db_id}/close`)).data;
