import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectImages } from "./ProjectImages";
import { projectsApi } from "../../services/projects";
import type { Project, ProjectImage } from "../../types";

function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    title: "ELORA",
    slug: "elora",
    short_description: null,
    problem: "Черновик, который ещё не сохранён",
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

const IMAGE: ProjectImage = {
  id: "22222222-2222-2222-2222-222222222222",
  url: "/uploads/photo.jpg",
  alt_text: null,
  sort_order: 0,
};

describe("ProjectImages", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("keeps unsaved case text when an image is set as the cover", async () => {
    // The bug this pins: the PUT response is the last *saved* project, so
    // feeding it back into editor state silently discarded the author's
    // unsaved paragraph. The component must patch only the cover field.
    const project = makeProject({ images: [IMAGE] });
    const serverCopy = makeProject({ images: [IMAGE], problem: "Старая сохранённая версия" });
    vi.spyOn(projectsApi, "update").mockResolvedValue(serverCopy);

    let latest = project;
    const onProjectChange = vi.fn((updater: (p: Project) => Project) => {
      latest = updater(latest);
    });

    render(
      <ProjectImages
        project={latest}
        onProjectChange={onProjectChange}
        onError={() => undefined}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Сделать обложкой" }));

    await waitFor(() => expect(projectsApi.update).toHaveBeenCalled());
    // The unsaved text survived and only the cover changed.
    expect(latest.cover_image_url).toBe("/uploads/photo.jpg");
    expect(latest.problem).toBe("Черновик, который ещё не сохранён");
  });

  it("reports a failed cover change instead of failing silently", async () => {
    const project = makeProject({ images: [IMAGE] });
    vi.spyOn(projectsApi, "update").mockRejectedValue(new Error("network"));

    const onError = vi.fn();
    render(
      <ProjectImages project={project} onProjectChange={() => undefined} onError={onError} />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Сделать обложкой" }));

    await waitFor(() =>
      expect(onError).toHaveBeenCalledWith("Не удалось установить обложку."),
    );
  });

  it("clears the cover when the cover image itself is deleted", async () => {
    const project = makeProject({ images: [IMAGE], cover_image_url: IMAGE.url });
    vi.spyOn(projectsApi, "deleteImage").mockResolvedValue(undefined);

    let latest = project;
    render(
      <ProjectImages
        project={latest}
        onProjectChange={(updater) => {
          latest = updater(latest);
        }}
        onError={() => undefined}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Удалить" }));

    await waitFor(() => expect(projectsApi.deleteImage).toHaveBeenCalled());
    expect(latest.images).toHaveLength(0);
    expect(latest.cover_image_url).toBeNull();
  });
});
