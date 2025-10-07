// frontend/src/api/limits.ts

import { api } from "./client";

export interface LimitsData {
  follow: {
    per_hour: number;
    per_day: number;
    warmup?: boolean;
  };
  unfollow: {
    per_hour: number;
    per_day: number;
  };
  like: {
    per_hour: number;
    per_day: number;
  };
  dm: {
    per_hour: number;
    per_day: number;
  };
  random_delay_ms: [number, number];
  block_cooldown_minutes: number;
}

export interface AccountLimits {
  account_id: number;
  handle: string;
  status: string;
  limits: LimitsData;
  has_custom_limits: boolean;
}

export interface AllAccountsLimitsResponse {
  accounts: AccountLimits[];
}

export interface LimitsResponse {
  account_id: number;
  limits_json: LimitsData;
}

export interface UpdateLimitsRequest {
  limits_json: LimitsData;
}

export interface UpdateLimitsResponse {
  ok: boolean;
}

export interface ResetLimitsResponse {
  ok: boolean;
  message: string;
}

/**
 * Get limits for a specific account
 */
export const getAccountLimits = async (accountId: number): Promise<LimitsData> => {
  const response = await api.get<LimitsResponse>(`/actions/limits/${accountId}`);
  return response.data.limits_json;
};

/**
 * Update limits for a specific account
 */
export const updateAccountLimits = async (
  accountId: number, 
  limits: LimitsData
): Promise<void> => {
  const request: UpdateLimitsRequest = { limits_json: limits };
  await api.put<UpdateLimitsResponse>(`/actions/limits/${accountId}`, request);
};

/**
 * Get limits for all accounts
 */
export const getAllAccountsLimits = async (): Promise<AccountLimits[]> => {
  const response = await api.get<AllAccountsLimitsResponse>("/actions/limits");
  return response.data.accounts;
};

/**
 * Reset account limits to defaults
 */
export const resetAccountLimits = async (accountId: number): Promise<string> => {
  const response = await api.post<ResetLimitsResponse>(`/actions/limits/${accountId}/reset`);
  return response.data.message;
};

/**
 * Get default limits (for reference)
 */
export const getDefaultLimits = (): LimitsData => {
  return {
    follow: { per_hour: 20, per_day: 100, warmup: true },
    unfollow: { per_hour: 20, per_day: 100 },
    like: { per_hour: 60, per_day: 400 },
    dm: { per_hour: 10, per_day: 50 },
    random_delay_ms: [800, 3000],
    block_cooldown_minutes: 60,
  };
};
