import { API_BASE, api } from "./api";

export interface AnalyticsDailyPoint {
  date: string;
  views: number;
}

export interface AnalyticsSource {
  source: string;
  views: number;
}

export interface AnalyticsTopProject {
  id: string;
  title: string;
  slug: string;
  views: number;
}

export interface AnalyticsRecentVisit {
  date: string;
  source: string;
  device: string;
  path: string;
  project_title: string | null;
  project_slug: string | null;
}

export interface AnalyticsSummary {
  window_days: number;
  total_views: number;
  window_views: number;
  daily: AnalyticsDailyPoint[];
  sources: AnalyticsSource[];
  top_projects: AnalyticsTopProject[];
  direct_views: number;
  recent: AnalyticsRecentVisit[];
}

export interface GitHubRepo {
  name: string;
  description: string;
  url: string;
  language: string | null;
  stars: number;
  forks: number;
  updated_at: string | null;
  topics: string[];
  homepage: string;
  archived: boolean;
}

export const analyticsApi = {
  summary: (days = 30) => api.get<AnalyticsSummary>(`/analytics?days=${days}`),
};

export const exportApi = {
  /** Triggers a browser download of the full account export. */
  download: () => {
    const link = document.createElement("a");
    // The session lives in an httpOnly cookie, so a plain navigation keeps it.
    link.href = `${API_BASE}/export`;
    link.rel = "noopener";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },
};

export const githubApi = {
  repos: (username: string) =>
    api.get<{ repos: GitHubRepo[]; count: number }>(
      `/github/repos?username=${encodeURIComponent(username)}`,
    ),
};
