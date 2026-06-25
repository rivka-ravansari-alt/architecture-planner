import { authApi } from "./authApi.js";
import { projectApi } from "./projectApi.js";

export const api = {
  ...authApi,
  ...projectApi,
};
