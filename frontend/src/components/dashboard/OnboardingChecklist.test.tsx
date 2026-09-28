import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { OnboardingChecklist } from "./OnboardingChecklist";
import type { Profile, Project } from "../../types";

function makeProfile(overrides: Partial<Profile> = {}): Profile {
  return {
    id: "p1",
    display_name: null,
    headline: null,
    bio: null,
    avatar_url: null,
    location: null,
    website_url: null,
    github_url: null,
    linkedin_url: null,
    telegram_url: null,
    theme: "classic",
    view_count: 0,
    ...overrides,
  };
}

function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: "pr1",
    title: "Проект",
    slug: "proekt",
    short_description: null,
    problem: null,
    solution: null,
    features: null,
    result: null,
    role: null,
    cover_image_url: null,
    github_url: null,
    live_url: null,
    status: "DRAFT",
    sort_order: 0,
    view_count: 0,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    published_at: null,
    technologies: [],
    images: [],
    ...overrides,
  };
}

function renderChecklist(profile: Profile, projects: Project[]) {
  return render(
    <MemoryRouter>
      <OnboardingChecklist profile={profile} projects={projects} />
    </MemoryRouter>,
  );
}

describe("OnboardingChecklist", () => {
  it("counts only a published project as done — a draft is not enough", () => {
    renderChecklist(
      makeProfile({ display_name: "Дмитрий К.", headline: "Full-Stack", bio: "Обо мне" }),
      [makeProject({ status: "DRAFT" })],
    );

    // profile + bio done, project exists, publication not done.
    expect(screen.getByText("3/4")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /опубликовать/i })).toBeInTheDocument();
  });

  it("hides itself once the portfolio is complete", () => {
    const { container } = renderChecklist(
      makeProfile({ display_name: "Дмитрий К.", headline: "Full-Stack", bio: "Обо мне" }),
      [makeProject({ status: "PUBLISHED" })],
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("sends a brand new account to the create-project form", () => {
    renderChecklist(makeProfile(), []);

    expect(screen.getByText("0/4")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /создать проект/i }),
    ).toHaveAttribute("href", "/dashboard/projects/new");
  });
});
