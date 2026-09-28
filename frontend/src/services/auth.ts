import { api } from "./api";
import type { User } from "../types";

export const authApi = {
  register: (email: string, username: string, password: string) =>
    api.post<{ user: User }>("/auth/register", { email, username, password }),

  login: (email: string, password: string) =>
    api.post<{ user: User }>("/auth/login", { email, password }),

  logout: () => api.post<void>("/auth/logout"),

  me: () => api.get<User>("/auth/me"),

  changePassword: (currentPassword: string, newPassword: string) =>
    api.put<void>("/auth/password", {
      current_password: currentPassword,
      new_password: newPassword,
    }),

  changeEmail: (email: string, password: string) =>
    api.put<User>("/auth/email", { email, password }),

  deleteAccount: (password: string) =>
    api.deleteWithBody<void>("/auth/account", { password }),

  resetRequest: (email: string) =>
    api.post<{ detail: string; dev_code: string | null }>("/auth/reset-request", {
      email,
    }),

  resetConfirm: (email: string, code: string, newPassword: string) =>
    api.post<void>("/auth/reset-confirm", { email, code, new_password: newPassword }),
};
