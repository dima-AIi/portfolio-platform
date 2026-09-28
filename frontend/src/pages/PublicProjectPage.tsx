import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorBanner } from "../components/ui/ErrorBanner";
import { TechBadge } from "../components/ui/TechBadge";
import { CaseText } from "../components/project/CaseText";
import { useSeo } from "../hooks/useSeo";
import { ApiError } from "../services/api";
import { portfolioApi } from "../services/portfolio";
import type { PublicProject } from "../types";

export function PublicProjectPage() {
  const { username, slug } = useParams<{ username: string; slug: string }>();
  const [data, setData] = useState<PublicProject | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!username || !slug) return;
    setLoading(true);
    portfolioApi
      .getPublicProject(username, slug)
      .then(setData)
      .catch((err) =>
        setError(
          err instanceof ApiError && err.status === 404 ? "not-found" : "Не удалось загрузить проект.",
        ),
      )
      .finally(() => setLoading(false));
  }, [username, slug]);

  useSeo({
    title: data ? `${data.project.title} — ${data.username}` : "Проект — Portfolio Platform",
    description: data?.project.short_description ?? data?.project.result ?? null,
    image: data?.project.cover_image_url ?? null,
    type: "article",
    canonicalPath: username && slug ? `/${username}/projects/${slug}` : null,
  });

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
        <h1>Проект не найден</h1>
        <p>Проект не существует или ещё не опубликован.</p>
        <Link to={`/${username}`} className="btn btn-primary">
          Вернуться в портфолио
        </Link>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="container" style={{ paddingTop: 40 }}>
        <ErrorBanner message={error ?? "Ошибка загрузки."} />
      </div>
    );
  }

  const { project } = data;

  return (
    <article className={`pf-project-page pf-theme-${data.theme ?? "classic"}`}>
      <div className="container pf-project-container">
        <Link to={`/${username}`} className="pf-back-link">
          ← Вернуться в портфолио
        </Link>

        {project.cover_image_url && (
          <img src={project.cover_image_url} alt="" className="pf-cover" />
        )}

        <h1>{project.title}</h1>
        {project.short_description && <p className="pf-lead">{project.short_description}</p>}

        {project.technologies.length > 0 && (
          <div className="tech-row" style={{ margin: "16px 0 8px" }}>
            {project.technologies.map((t) => (
              <TechBadge key={t.id} name={t.name} />
            ))}
          </div>
        )}

        <div className="pf-case">
          {project.problem && (
            <section className="pf-case-section">
              <h4>Проблема</h4>
              <CaseText text={project.problem} />
            </section>
          )}
          {project.solution && (
            <section className="pf-case-section">
              <h4>Решение</h4>
              <CaseText text={project.solution} />
            </section>
          )}
          {project.role && (
            <section className="pf-case-section">
              <h4>Моя роль</h4>
              <p>{project.role}</p>
            </section>
          )}
          {project.features && (
            <section className="pf-case-section">
              <h4>Функции</h4>
              <CaseText text={project.features} linesAsList />
            </section>
          )}
          {project.result && (
            <section className="pf-case-section">
              <h4>Результат</h4>
              <CaseText text={project.result} />
            </section>
          )}
        </div>

        {project.images.length > 1 && (
          <section className="pf-gallery">
            <h4>Галерея</h4>
            <div className="pf-gallery-grid">
              {project.images.map((image) => (
                <img key={image.id} src={image.url} alt={image.alt_text ?? ""} loading="lazy" />
              ))}
            </div>
          </section>
        )}

        <div className="pf-project-links">
          {project.live_url && (
            <a href={project.live_url} target="_blank" rel="noreferrer" className="btn btn-primary btn-lg">
              Смотреть live demo ↗
            </a>
          )}
          {project.github_url && (
            <a
              href={project.github_url}
              target="_blank"
              rel="noreferrer"
              className="btn btn-secondary btn-lg"
            >
              Исходный код ↗
            </a>
          )}
        </div>
      </div>
    </article>
  );
}
