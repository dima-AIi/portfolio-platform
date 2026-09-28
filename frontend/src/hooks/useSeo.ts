import { useEffect } from "react";

interface SeoOptions {
  title: string;
  description?: string | null;
  image?: string | null;
  /** "website" for portfolios/landing, "article" for a single project case. */
  type?: "website" | "article";
  canonicalPath?: string | null;
}

const SITE_NAME = "Portfolio Platform";

/** Serialize a value into a <script type="application/ld+json"> block. */
function setJsonLd(id: string, data: unknown | null) {
  let el = document.getElementById(id) as HTMLScriptElement | null;
  if (!data) {
    el?.remove();
    return;
  }
  if (!el) {
    el = document.createElement("script");
    el.id = id;
    el.type = "application/ld+json";
    document.head.appendChild(el);
  }
  el.textContent = JSON.stringify(data);
}

function absolute(url: string | null): string | undefined {
  if (!url) return undefined;
  return new URL(url, window.location.origin).href;
}

/**
 * JSON-LD Person + ProfilePage markup for a public portfolio.
 *
 * Search engines use this to show a name, job title and links directly in
 * results, which is the main payoff of a public portfolio being crawlable.
 */
export function usePersonSchema(portfolio: {
  username: string;
  profile: {
    display_name: string | null;
    headline: string | null;
    bio: string | null;
    avatar_url: string | null;
    website_url: string | null;
    github_url: string | null;
    linkedin_url: string | null;
    telegram_url: string | null;
  };
  skills: string[];
  projects: { id: string; title: string; slug: string }[];
} | null) {
  useEffect(() => {
    if (!portfolio) {
      setJsonLd("ld-person", null);
      return;
    }
    const { profile } = portfolio;
    const name = profile.display_name || `@${portfolio.username}`;
    const pageUrl = new URL(`/${portfolio.username}`, window.location.origin).href;
    const sameAs = [
      absolute(profile.website_url),
      absolute(profile.github_url),
      absolute(profile.linkedin_url),
      absolute(profile.telegram_url),
    ].filter((url): url is string => Boolean(url));

    setJsonLd("ld-person", {
      "@context": "https://schema.org",
      "@graph": [
        {
          "@type": "Person",
          name,
          url: pageUrl,
          ...(profile.headline ? { jobTitle: profile.headline } : {}),
          ...(profile.bio ? { description: profile.bio } : {}),
          ...(absolute(profile.avatar_url) ? { image: absolute(profile.avatar_url) } : {}),
          ...(sameAs.length ? { sameAs } : {}),
          ...(portfolio.skills.length ? { knowsAbout: portfolio.skills } : {}),
        },
        {
          "@type": "ProfilePage",
          url: pageUrl,
          name: `${name} — Портфолио`,
          ...(profile.headline ? { about: { "@type": "Person", name, jobTitle: profile.headline } } : {}),
          isPartOf: { "@type": "WebSite", name: SITE_NAME, url: window.location.origin },
        },
        {
          // The project list as its own node, so the portfolio can surface as a
          // list of case studies rather than an unlabelled set of links.
          "@type": "ItemList",
          name: `Проекты — ${name}`,
          ...(portfolio.projects.length
            ? {
                itemListElement: portfolio.projects.map((project, index) => ({
                  "@type": "ListItem",
                  position: index + 1,
                  url: new URL(
                    `/${portfolio.username}/projects/${project.slug}`,
                    window.location.origin,
                  ).href,
                  name: project.title,
                })),
              }
            : {}),
        },
      ],
    });
  }, [portfolio]);
}

// Used when a page has nothing specific to say. A generic description still
// ranks better than an empty <meta name="description">, and it replaces the
// previous page's text instead of leaking it onto this one.
const DEFAULT_DESCRIPTION =
  "Портфолио специалиста с реальными проектами: проблема, решение, результат и технологии.";

function setMeta(attr: "name" | "property", key: string, content: string) {
  let el = document.head.querySelector<HTMLMetaElement>(`meta[${attr}="${key}"]`);
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute(attr, key);
    document.head.appendChild(el);
  }
  el.setAttribute("content", content);
}

function setCanonical(href: string | null) {
  let el = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  if (!href) {
    el?.remove();
    return;
  }
  if (!el) {
    el = document.createElement("link");
    el.rel = "canonical";
    document.head.appendChild(el);
  }
  el.href = href;
}

export function useSeo({ title, description, image, type = "website", canonicalPath }: SeoOptions) {
  useEffect(() => {
    document.title = title;
    const canonical = canonicalPath ?? window.location.pathname;
    const url = new URL(window.location.origin + canonical).href;
    const absoluteImage = image ? new URL(image, window.location.origin).href : null;

    setCanonical(url);
    setMeta("property", "og:title", title);
    setMeta("property", "og:type", type);
    setMeta("property", "og:url", url);
    setMeta("property", "og:site_name", SITE_NAME);
    setMeta("property", "og:locale", "ru_RU");
    setMeta("name", "twitter:card", absoluteImage ? "summary_large_image" : "summary");
    setMeta("name", "twitter:title", title);

    // Descriptions are always set: to the page's own text, or to a generic
    // fallback. Never left empty and never left holding the previous page's
    // value, which would be a stale description for a different URL.
    const metaDescription = description || DEFAULT_DESCRIPTION;
    setMeta("name", "description", metaDescription);
    setMeta("property", "og:description", metaDescription);
    setMeta("name", "twitter:description", metaDescription);

    // A wrong image is worse than no image, so og:image is dropped instead of
    // being carried over from the previously visited page.
    if (absoluteImage) {
      setMeta("property", "og:image", absoluteImage);
      setMeta("name", "twitter:image", absoluteImage);
    } else {
      for (const el of document.head.querySelectorAll(
        'meta[property="og:image"], meta[name="twitter:image"]',
      )) {
        el.remove();
      }
    }
  }, [title, description, image, type, canonicalPath]);
}
