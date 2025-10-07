import { api } from "./client";

export type AccountRow = { 
  id: number; 
  handle: string; 
  bulk_profile_name?: string | null;
  health?: string | null;
  instagram_username?: string | null;
  last_ws_puppeteer?: string | null;
  last_opened_at?: string | null;
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

export const syncUsername = async (accountId: number): Promise<{instagram_username: string | null, message: string}> => {
  console.log(`[syncUsername] Syncing username for account ${accountId}`);
  const response = await api.post(`/engine/sync-username?profile_id=${accountId}`);
  console.log("[syncUsername] Response:", response.data);
  return response.data;
};

export type BulkSyncResult = {
  count: number;
  updated: number;
  results: Array<{ id: number; status: string; instagram_username?: string; error?: string; via?: string }>;
};

export const syncUsernamesBulk = async (accountIds: number[], concurrency = 5): Promise<BulkSyncResult> => {
  const response = await api.post(`/engine/sync-usernames-bulk`, {
    account_ids: accountIds,
    concurrency,
  });
  return response.data as BulkSyncResult;
};

export const wsCheckProfile = async (profile_id: number) => 
  (await api.get(`/profiles/${profile_id}/ws-check`)).data;

// Account creation functions
export const createAccount = async (handle: string) => {
  return (await api.post(`/accounts/create-simple?handle=${encodeURIComponent(handle)}`)).data;
};

export const createBulkAccounts = async (count: number, prefix: string = 'account') => {
  const response = await api.post(`/accounts/create-bulk?prefix=${encodeURIComponent(prefix)}&count=${count}`);
  return response.data.accounts;
};

export const deleteAccount = async (id: number) => {
  return (await api.delete(`/accounts/${id}`)).data;
};

export const getUnlinkedAccounts = async () => {
  return (await api.get('/accounts/unlinked')).data;
};

export const deleteUnlinkedAccounts = async () => {
  return (await api.delete('/accounts/unlinked')).data;
};

// Orphaned link cleanup functions
export const detectOrphanedLinks = async () => {
  return (await api.get('/accounts/orphaned-links')).data;
};

export const cleanupOrphanedLinks = async () => {
  return (await api.post('/accounts/cleanup-orphaned-links')).data;
};

export const cleanupSelectedOrphanedLinks = async (accountIds: number[]) => {
  return (await api.post('/accounts/cleanup-orphaned-links-selected', accountIds)).data;
};

// Auto cleanup settings
export const getAutoCleanupSettings = async () => {
  return (await api.get('/accounts/auto-cleanup-settings')).data;
};

export const updateAutoCleanupSettings = async (enabled: boolean, intervalSeconds: number = 5) => {
  return (await api.post('/accounts/auto-cleanup-settings', {
    enabled,
    interval_seconds: intervalSeconds
  })).data;
};
