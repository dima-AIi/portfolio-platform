import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { usePersonSchema, useSeo } from "./useSeo";

function jsonLd(id: string): Record<string, unknown> | null {
  const el = document.getElementById(id);
  return el ? JSON.parse(el.textContent ?? "{}") : null;
}

function metaContent(selector: string): string | null {
  return document.head.querySelector(selector)?.getAttribute("content") ?? null;
}

function canonicalHref(): string | null {
  return document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]')?.href ?? null;
}

describe("useSeo", () => {
  it("sets title and basic Open Graph tags", () => {
    renderHook(() =>
      useSeo({ title: "Телеграм CRM — Портфолио", description: "Кейс про CRM", image: "/uploads/a.png" }),
    );

    expect(document.title).toBe("Телеграм CRM — Портфолио");
    expect(metaContent('meta[property="og:title"]')).toBe("Телеграм CRM — Портфолио");
    expect(metaContent('meta[property="og:type"]')).toBe("website");
    expect(metaContent('meta[property="og:site_name"]')).toBe("Portfolio Platform");
  });

  it("resolves a relative image to an absolute URL", () => {
    renderHook(() => useSeo({ title: "T", image: "/uploads/cover.png" }));

    const expected = new URL("/uploads/cover.png", window.location.origin).href;
    expect(metaContent('meta[property="og:image"]')).toBe(expected);
    expect(metaContent('meta[name="twitter:card"]')).toBe("summary_large_image");
  });

  it("falls back to a summary card when there is no image", () => {
    renderHook(() => useSeo({ title: "T" }));
    expect(metaContent('meta[name="twitter:card"]')).toBe("summary");
  });

  it("builds a canonical URL from the given path", () => {
    renderHook(() => useSeo({ title: "T", canonicalPath: "/dmitriy/projects/crm" }));

    expect(canonicalHref()).toBe(
      new URL("/dmitriy/projects/crm", window.location.origin).href,
    );
  });

  it("uses article type for a project page", () => {
    renderHook(() => useSeo({ title: "T", type: "article" }));
    expect(metaContent('meta[property="og:type"]')).toBe("article");
  });

  it("replaces the previous page description instead of leaking it", () => {
    const { rerender } = renderHook<unknown, { description: string | null }>(
      ({ description }: { description: string | null }) => useSeo({ title: "T", description }),
      { initialProps: { description: "Описание прошлой страницы" } },
    );
    expect(metaContent('meta[name="description"]')).toBe("Описание прошлой страницы");

    rerender({ description: null });

    // Must not stay empty — a generic description still beats a missing one.
    const fallback = metaContent('meta[name="description"]');
    expect(fallback).toBeTruthy();
    expect(fallback).not.toBe("Описание прошлой страницы");
  });

  it("drops a stale og:image when the next page has none", () => {
    const { rerender } = renderHook<unknown, { image: string | null }>(
      ({ image }: { image: string | null }) => useSeo({ title: "T", image }),
      { initialProps: { image: "/uploads/old.png" } },
    );
    expect(metaContent('meta[property="og:image"]')).not.toBeNull();

    rerender({ image: null });

    expect(metaContent('meta[property="og:image"]')).toBeNull();
    expect(metaContent('meta[name="twitter:image"]')).toBeNull();
  });

  it("does not duplicate tags on re-render", () => {
    const { rerender } = renderHook(() => useSeo({ title: "T", description: "D" }));
    rerender();
    rerender();

    expect(document.head.querySelectorAll('meta[name="description"]')).toHaveLength(1);
    expect(document.head.querySelectorAll('link[rel="canonical"]')).toHaveLength(1);
  });
});
describe("usePersonSchema", () => {
  const portfolio = {
    username: "dmitriy",
    profile: {
      display_name: "Dmitriy K.",
      headline: "Python & Full-Stack Developer",
      bio: "I build automation tools.",
      avatar_url: "/uploads/avatar.png",
      website_url: "https://dmitriy.example.com",
      github_url: "https://github.com/dmitriy",
      linkedin_url: null,
      telegram_url: "https://t.me/dmitriy",
    },
    skills: ["Python", "FastAPI"],
    projects: [
      { id: "1", title: "Telegram CRM", slug: "telegram-crm" },
      { id: "2", title: "Analytics", slug: "analytics" },
    ],
  };

  function graph(index: number) {
    const data = jsonLd("ld-person");
    return (data?.["@graph"] as Record<string, unknown>[])[index];
  }

  it("lists the projects as an ItemList with absolute URLs", () => {
    renderHook(() => usePersonSchema(portfolio));

    const list = graph(2);
    expect(list["@type"]).toBe("ItemList");
    const items = list.itemListElement as { position: number; url: string; name: string }[];
    expect(items).toHaveLength(2);
    expect(items[0].position).toBe(1);
    expect(items[0].url).toBe(
      new URL("/dmitriy/projects/telegram-crm", window.location.origin).href,
    );
    expect(items[1].name).toBe("Analytics");
  });

  it("omits itemListElement when the portfolio has no projects", () => {
    renderHook(() => usePersonSchema({ ...portfolio, projects: [] }));
    expect(graph(2).itemListElement).toBeUndefined();
  });
  it("emits a Person node with name, role and skills", () => {
    renderHook(() => usePersonSchema(portfolio));

    const person = graph(0);
    expect(person["@type"]).toBe("Person");
    expect(person.name).toBe("Dmitriy K.");
    expect(person.jobTitle).toBe("Python & Full-Stack Developer");
    expect(person.knowsAbout).toEqual(["Python", "FastAPI"]);
  });

  it("resolves relative image and profile links to absolute URLs", () => {
    renderHook(() => usePersonSchema(portfolio));

    const person = graph(0);
    const expectedImage = new URL("/uploads/avatar.png", window.location.origin).href;
    expect(person.image).toBe(expectedImage);
    expect((person.sameAs as string[]).every((u) => u.startsWith("http"))).toBe(true);
  });

  it("omits sameAs entirely when no social links are set", () => {
    renderHook(() =>
      usePersonSchema({
        ...portfolio,
        profile: { ...portfolio.profile, website_url: null, github_url: null, telegram_url: null },
      }),
    );

    expect(graph(0).sameAs).toBeUndefined();
  });

  it("falls back to the username when no display name is set", () => {
    renderHook(() =>
      usePersonSchema({ ...portfolio, profile: { ...portfolio.profile, display_name: null } }),
    );

    expect(graph(0).name).toBe("@dmitriy");
  });

  it("adds a ProfilePage node linking back to the site", () => {
    renderHook(() => usePersonSchema(portfolio));

    const page = graph(1);
    expect(page["@type"]).toBe("ProfilePage");
    expect((page.isPartOf as Record<string, string>).name).toBe("Portfolio Platform");
  });

  it("removes the script when there is no portfolio", () => {
    const { rerender } = renderHook(
      ({ value }: { value: typeof portfolio | null }) => usePersonSchema(value),
      { initialProps: { value: portfolio as typeof portfolio | null } },
    );
    expect(jsonLd("ld-person")).not.toBeNull();

    rerender({ value: null });

    expect(jsonLd("ld-person")).toBeNull();
  });

  it("does not duplicate the script tag across renders", () => {
    const { rerender } = renderHook(() => usePersonSchema(portfolio));
    rerender();
    rerender();

    expect(document.querySelectorAll("#ld-person")).toHaveLength(1);
  });
});