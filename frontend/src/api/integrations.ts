import { api } from "./client";
export const getAdsPowerStatus = async () =>
  (await api.get("/integrations/adspower/status")).data; // whatever your backend returns
