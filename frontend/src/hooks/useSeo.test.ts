import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { useSeo } from "./useSeo";

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