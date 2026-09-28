import { api } from "./api";
import type { PublicPortfolio, PublicProject, Technology } from "../types";

export const portfolioApi = {
  technologies: () => api.get<Technology[]>("/technologies"),

  getPublic: (username: string) => api.get<PublicPortfolio>(`/public/${username}`),

  getPublicPage: (username: string, page: number, limit: number) =>
    api.get<PublicPortfolio>(`/public/${username}?page=${page}&limit=${limit}`),

  getPublicProject: (username: string, slug: string) =>
    api.get<PublicProject>(`/public/${username}/projects/${slug}`),
};
