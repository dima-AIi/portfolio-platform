import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorBanner } from "../components/ui/ErrorBanner";
import { RevealOnScroll } from "../components/ui/RevealOnScroll";
import { usePersonSchema, useSeo } from "../hooks/useSeo";
import { ApiError } from "../services/api";
import { portfolioApi } from "../services/portfolio";
import type { PublicPortfolio } from "../types";

const CONTACT_LABELS: Record<string, string> = {
  website_url: "Сайт",
  github_url: "GitHub",
  linkedin_url: "LinkedIn",
  telegram_url: "Telegram",
};

/** Projects shown before a "load more" control appears. */
const PAGE_SIZE = 9;

export function PublicPortfolioPage() {
  const { username } = useParams<{ username: string }>();
  const [portfolio, setPortfolio] = useState<PublicPortfolio | null>(null);
  const [visible, setVisible] = useState<PublicPortfolio["projects"]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!username) return;
    setLoading(true);
    setError(null);
    portfolioApi
      .getPublicPage(username, 1, PAGE_SIZE)
      .then((data) => {
        setPortfolio(data);
        setVisible(data.projects);
      })
      .catch((err) =>
        setError(
          err instanceof ApiError && err.status === 404 ? "not-found" : "Не удалось загрузить портфолио.",
        ),
      )
      .finally(() => setLoading(false));
  }, [username]);

  const loadMore = useCallback(async () => {
    if (!username || loadingMore) return;
    setLoadingMore(true);
    const nextPage = Math.floor(visible.length / PAGE_SIZE) + 1;
    try {
      const data = await portfolioApi.getPublicPage(username, nextPage, PAGE_SIZE);
      setVisible((current) => {
        // Guard against duplicates if two requests race on a slow connection.
        const seen = new Set(current.map((p) => p.id));
        return [...current, ...data.projects.filter((p) => !seen.has(p.id))];
      });
    } catch {
      /* keep what is already on screen */
    } finally {
      setLoadingMore(false);
    }
  }, [username, visible.length, loadingMore]);

  useSeo({
    title: portfolio
      ? `${portfolio.profile.display_name ?? `@${portfolio.username}`} — Портфолио`
      : "Портфолио — Portfolio Platform",
    description: portfolio?.profile.bio ?? null,
    image: portfolio?.profile.avatar_url ?? null,
    canonicalPath: username ? `/${username}` : null,
  });

  // Structured data helps search engines render a rich person/portfolio card.
  usePersonSchema(portfolio);

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
      </div>
    );
  }

  if (error === "not-found") {
    return (
      <div className="public-404 container">
        <h1>Портфолио не найдено</h1>
        <p>Портфолио по адресу /{username} не существует.</p>
        <Link to="/" className="btn btn-primary">
          Portfolio Platform ↗
        </Link>
      </div>
    );
  }

  if (error || !portfolio) {
    return (
      <div className="container" style={{ paddingTop: 40 }}>
        <ErrorBanner message={error ?? "Ошибка загрузки."} />
      </div>
    );
  }

  const { profile } = portfolio;
  const contacts = (["website_url", "github_url", "linkedin_url", "telegram_url"] as const).filter(
    (key) => profile[key],
  );

  return (
    <div className={`pf pf-theme-${profile.theme ?? "classic"}`}>
      <div className="container pf-actions no-print">
        <button type="button" className="btn btn-secondary btn-sm" onClick={() => window.print()}>
          Скачать PDF
        </button>
      </div>
      {/* Hero */}
      <section className="pf-hero">
        <div className="container pf-hero-inner">
          {profile.avatar_url ? (
            <img src={profile.avatar_url} alt="" className="pf-avatar" />
          ) : (
            <div className="pf-avatar pf-avatar-empty">
              {(profile.display_name ?? username ?? "?").charAt(0).toUpperCase()}
            </div>
          )}
          <div>
            <h1>{profile.display_name ?? `@${portfolio.username}`}</h1>
            {profile.headline && <p className="pf-headline">{profile.headline}</p>}
            {profile.location && <p className="pf-location">{profile.location}</p>}
            {contacts.length > 0 && (
              <div className="pf-contact-row">
                {contacts.map((key) => (
                  <a
                    key={key}
                    href={profile[key]!}
                    target="_blank"
                    rel="noreferrer"
                    className="badge badge-tech"
                  >
                    {CONTACT_LABELS[key]} ↗
                  </a>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      <div className="container pf-content">
        {/* О себе */}
        {profile.bio && (
          <RevealOnScroll className="pf-section">
            <h2>О себе</h2>
            <p className="pf-bio">{profile.bio}</p>
          </RevealOnScroll>
        )}

        {/* Технологии */}
        {portfolio.skills.length > 0 && (
          <RevealOnScroll className="pf-section">
            <h2>Технологии</h2>
            <div className="tech-row">
              {portfolio.skills.map((skill) => (
                <span key={skill} className="badge badge-tech">
                  {skill}
                </span>
              ))}
            </div>
          </RevealOnScroll>
        )}

        {/* Проекты */}
        <RevealOnScroll className="pf-section">
          <h2>Проекты</h2>
          {visible.length === 0 ? (
            <p className="muted">Опубликованных проектов пока нет.</p>
          ) : (
            <div className="pf-projects-grid">
              {visible.map((project, i) => (
                <Link
                  key={project.id}
                  to={`/${portfolio.username}/projects/${project.slug}`}
                  className="card pf-project-card"
                >
                  <div className="pf-project-cover">
                    {project.cover_image_url ? (
                      <img
                        src={project.cover_image_url}
                        alt=""
                        // The first card is above the fold — do not lazy-load it.
                        loading={i === 0 ? "eager" : "lazy"}
                        decoding="async"
                      />
                    ) : (
                      <div className="pf-project-cover-fallback">
                        {project.title.charAt(0).toUpperCase()}
                      </div>
                    )}
                  </div>
                  <div className="pf-project-body">
                    <h3 className="pf-project-title">{project.title}</h3>
                    <p className="pf-project-desc">{project.short_description}</p>
                    <div className="tech-row">
                      {project.technologies.slice(0, 4).map((t) => (
                        <span key={t.id} className="badge badge-tech">
                          {t.name}
                        </span>
                      ))}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
          {visible.length < portfolio.total && (
            <div className="pf-load-more no-print">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => void loadMore()}
                disabled={loadingMore}
              >
                {loadingMore
                  ? "Загрузка…"
                  : `Показать ещё (${portfolio.total - visible.length})`}
              </button>
            </div>
          )}
        </RevealOnScroll>

        {/* Контакты */}
        {contacts.length > 0 && (
          <RevealOnScroll className="pf-section pf-contacts">
            <h2>Связаться</h2>
            <p className="muted">Напишите мне по любому из каналов:</p>
            <div className="pf-contact-row">
              {contacts.map((key) => (
                <a
                  key={key}
                  href={profile[key]!}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-secondary"
                >
                  {CONTACT_LABELS[key]} ↗
                </a>
              ))}
            </div>
          </RevealOnScroll>
        )}
      </div>
    </div>
  );
}
