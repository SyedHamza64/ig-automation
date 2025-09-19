import { api } from "../api/client";

export type Account = {
  id: number;
  username: string;
  profile_id?: number | string | null;
  status?: string | null;
};

export const listAccounts = async () => (await api.get<Account[]>("/accounts")).data;

export const createAccount = async (body: { username: string; profile_id?: number | string }) =>
  (await api.post<Account>("/accounts", body)).data;

export const deleteAccount = async (id: number) =>
  (await api.delete(`/accounts/${id}`)).data;
