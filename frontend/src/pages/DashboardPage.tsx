import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";
import { CopyLinkButton } from "../components/ui/CopyLinkButton";
import { OnboardingChecklist } from "../components/dashboard/OnboardingChecklist";
import { firstName } from "../utils/firstName";
import { plural } from "../utils/plural";
import { profileApi } from "../services/profile";
import { projectsApi } from "../services/projects";
import type { Profile, Project } from "../types";

export function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<{ profile: Profile; projects: Project[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([profileApi.get(), projectsApi.list()])
      .then(([profile, projects]) => setData({ profile, projects: projects.items }))
      .catch(() => setError("Не удалось загрузить данные."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
      </div>
    );
  }

  if (error || !data) {
    return <div className="error-banner">{error ?? "Что-то пошло не так."}</div>;
  }

  const publishedProjects = data.projects.filter((p) => p.status === "PUBLISHED");
  const drafts = data.projects.length - publishedProjects.length;
  const name = firstName(data.profile.display_name);
  const profileFields = [
    data.profile.display_name,
    data.profile.headline,
    data.profile.bio,
    data.profile.avatar_url,
    data.profile.github_url || data.profile.telegram_url || data.profile.linkedin_url,
  ];
  const filled = profileFields.filter(Boolean).length;
  const completion = Math.round((filled / profileFields.length) * 100);

  // Most-viewed published case: the idea Folio uses to rank projects.
  const topProject = publishedProjects.reduce<Project | null>(
    (best, p) => (!best || p.view_count > best.view_count ? p : best),
    null,
  );
  const totalViews = publishedProjects.reduce((sum, p) => sum + p.view_count, 0);
  // A published project without a cover looks like a placeholder.
  const missingCovers = publishedProjects.filter((p) => !p.cover_image_url).length;

  return (
    <div className="page dashboard-page">
      <h1 className="page-title">
        {name ? `Здравствуйте, ${name}!` : "Добро пожаловать!"}
      </h1>
      <p className="page-subtitle">
        {publishedProjects.length > 0
          ? "Ваши проекты и то, как их видят посетители."
          : "Начните с одного проекта — остальное добавите по ходу."}
      </p>

      <OnboardingChecklist profile={data.profile} projects={data.projects} />

      <div className="stat-grid">
        <Link to="/dashboard/projects" className="card card-pad stat-card stat-link-card">
          <span className="stat-value">{data.projects.length}</span>
          <span className="stat-label">Проектов</span>
          <span className="stat-link">Управлять →</span>
        </Link>
        <div className="card card-pad stat-card">
          <span className="stat-value">{publishedProjects.length}</span>
          <span className="stat-label">Опубликовано</span>
        </div>
        <div className="card card-pad stat-card">
          <span className="stat-value">{drafts}</span>
          <span className="stat-label">Черновиков</span>
        </div>
        <div className="card card-pad stat-card">
          <span className="stat-value">{data.profile.view_count}</span>
          <span className="stat-label">Просмотров страницы</span>
        </div>
        <Link to="/dashboard/profile" className="card card-pad stat-card stat-link-card">
          <span className="stat-value">{completion}%</span>
          <span className="stat-label">Профиль заполнен</span>
          <span className="stat-link">Редактировать →</span>
        </Link>
      </div>

      {publishedProjects.length > 0 && (
        <section className="dash-section">
          <h2 className="dash-section-title">Ваши проекты</h2>
          <div className="dash-projects">
            {publishedProjects.slice(0, 4).map((p) => (
              <div key={p.id} className="card card-pad dash-project">
                <div className="dash-project-cover">
                  {p.cover_image_url ? (
                    <img src={p.cover_image_url} alt="" loading="lazy" />
                  ) : (
                    <span className="dash-project-cover-empty">Нет фото</span>
                  )}
                </div>
                <div className="dash-project-main">
                  <strong>{p.title}</strong>
                  <span className="muted">
                    {p.view_count} {plural(p.view_count, "просмотр", "просмотра", "просмотров")}
                  </span>
                  {p.live_url && (
                    <a
                      href={p.live_url}
                      target="_blank"
                      rel="noreferrer"
                      className="dash-project-link"
                    >
                      Открыть сайт ↗
                    </a>
                  )}
                </div>
                <Link
                  to={`/dashboard/projects/${p.id}`}
                  className="btn btn-secondary btn-sm"
                >
                  Изменить
                </Link>
              </div>
            ))}
          </div>
          <div className="dash-section-foot">
            <Link to="/dashboard/projects" className="btn btn-secondary btn-sm">
              Все проекты →
            </Link>
            <Link to="/dashboard/projects/new" className="btn btn-primary btn-sm">
              + Добавить проект
            </Link>
          </div>
        </section>
      )}

      <section className="dash-section">
        <h2 className="dash-section-title">
          {publishedProjects.length === 0 ? "С чего начать" : "Что улучшить"}
        </h2>
        <div className="dash-tips">
          {publishedProjects.length === 0 ? (
            <div className="card card-pad dash-tip dash-tip-accent">
              <strong>Добавьте первый проект</strong>
              <p className="muted">
                Каждый проект — это кейс: Проблема, Решение, Результат и Технологии.
                Начните с одного — остальные добавите по ходу.
              </p>
              <Link to="/dashboard/projects/new" className="btn btn-primary">
                Создать проект
              </Link>
            </div>
          ) : (
            <>
              {drafts > 0 && (
                <div className="card card-pad dash-tip">
                  <strong>Черновики ждут публикации</strong>
                  <p className="muted">
                    Их {drafts}. Черновик виден только вам — опубликуйте, чтобы проект
                    появился на странице.
                  </p>
                  <Link to="/dashboard/projects" className="btn btn-secondary btn-sm">
                    Опубликовать
                  </Link>
                </div>
              )}
              {missingCovers > 0 && (
                <div className="card card-pad dash-tip">
                  <strong>Добавьте обложки к {missingCovers} проектам</strong>
                  <p className="muted">
                    Проект без фото читается как заглушка. Обложка — первое, что видит
                    посетитель.
                  </p>
                  <Link to="/dashboard/projects" className="btn btn-secondary btn-sm">
                    Добавить фото
                  </Link>
                </div>
              )}
              {completion < 100 && (
                <div className="card card-pad dash-tip">
                  <strong>Профиль заполнен на {completion}%</strong>
                  <p className="muted">
                    Имя, специализация и пара слов о себе — минимум, чтобы вас запомнили.
                  </p>
                  <Link to="/dashboard/profile" className="btn btn-secondary btn-sm">
                    Дополнить
                  </Link>
                </div>
              )}
              {topProject && topProject.view_count > 0 && (
                <div className="card card-pad dash-tip">
                  <strong>«{topProject.title}» — самый популярный кейс</strong>
                  <p className="muted">
                    {topProject.view_count}{" "}
                    {plural(topProject.view_count, "просмотр", "просмотра", "просмотров")} из{" "}
                    {totalViews}. Попробуете поднять остальные так же?
                  </p>
                  <Link
                    to={`/dashboard/projects/${topProject.id}`}
                    className="btn btn-secondary btn-sm"
                  >
                    Посмотреть кейс
                  </Link>
                </div>
              )}
            </>
          )}
        </div>
      </section>

      <div className="dashboard-actions">
        <div className="card card-pad">
          <h3>Поделитесь портфолио</h3>
          <p className="muted">
            Ваша публичная страница: <strong>/{user?.username}</strong>
          </p>
          <div className="share-actions">
            {user && <CopyLinkButton to={`/${user.username}`} />}
            {user && (
              <Link to={`/${user.username}`} className="btn btn-secondary">
                Открыть публичную страницу ↗
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
