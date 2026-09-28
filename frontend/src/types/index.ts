export type ProjectStatus = "DRAFT" | "PUBLISHED";

export interface User {
  id: string;
  email: string;
  username: string;
}

/** Login/register reply. The JWT is not exposed to the page — it is set as an
 *  httpOnly cookie by the backend, so it cannot be read by JavaScript. */
export interface AuthResponse {
  user: User;
}

export interface Profile {
  id: string;
  display_name: string | null;
  headline: string | null;
  bio: string | null;
  avatar_url: string | null;
  location: string | null;
  website_url: string | null;
  github_url: string | null;
  linkedin_url: string | null;
  telegram_url: string | null;
  theme: string;
  view_count: number;
}

export interface Technology {
  id: string;
  name: string;
  slug: string;
  category: string | null;
}

export interface ProjectImage {
  id: string;
  url: string;
  alt_text: string | null;
  sort_order: number;
}

export interface Project {
  id: string;
  title: string;
  slug: string;
  short_description: string | null;
  problem: string | null;
  solution: string | null;
  features: string | null;
  result: string | null;
  role: string | null;
  cover_image_url: string | null;
  github_url: string | null;
  live_url: string | null;
  status: ProjectStatus;
  sort_order: number;
  view_count: number;
  created_at: string;
  updated_at: string;
  published_at: string | null;
  technologies: Technology[];
  images: ProjectImage[];
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
}

export interface ProjectPayload {
  title: string;
  short_description?: string | null;
  problem?: string | null;
  solution?: string | null;
  features?: string | null;
  result?: string | null;
  role?: string | null;
  github_url?: string | null;
  live_url?: string | null;
  cover_image_url?: string | null;
}

export interface PublicPortfolio {
  username: string;
  profile: Profile;
  projects: Project[];
  skills: string[];
  /** Total published projects, so the UI knows whether more exist. */
  total: number;
  page: number | null;
  limit: number | null;
}

export interface PublicProject {
  username: string;
  theme: string;
  project: Project;
}

export interface ApiErrorPayload {
  error: {
    code: string;
    message: string;
  };
}
