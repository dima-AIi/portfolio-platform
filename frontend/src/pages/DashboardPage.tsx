import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";
import { CopyLinkButton } from "../components/ui/CopyLinkButton";
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

  const published = data.projects.filter((p) => p.status === "PUBLISHED").length;
  const drafts = data.projects.length - published;
  const profileFields = [
    data.profile.display_name,
    data.profile.headline,
    data.profile.bio,
    data.profile.avatar_url,
    data.profile.github_url || data.profile.telegram_url || data.profile.linkedin_url,
  ];
  const filled = profileFields.filter(Boolean).length;
  const completion = Math.round((filled / profileFields.length) * 100);

  return (
    <div className="page dashboard-page">
      <h1 className="page-title">
        Здравствуйте{data.profile.display_name ? `, ${data.profile.display_name}` : ""}!
      </h1>
      <p className="page-subtitle">Текущее состояние вашего портфолио.</p>

      <div className="stat-grid">
        <div className="card card-pad stat-card">
          <span className="stat-value">{data.projects.length}</span>
          <span className="stat-label">Проектов</span>
          <Link to="/dashboard/projects" className="stat-link">
            Управлять →
          </Link>
        </div>
        <div className="card card-pad stat-card">
          <span className="stat-value">{published}</span>
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
        <div className="card card-pad stat-card">
          <span className="stat-value">{completion}%</span>
          <span className="stat-label">Профиль заполнен</span>
          <Link to="/dashboard/profile" className="stat-link">
            Редактировать →
          </Link>
        </div>
      </div>

      <div className="dashboard-actions">
        <div className="card card-pad">
          <h3>Добавьте первый проект</h3>
          <p className="muted">
            Каждый проект — это кейс: Проблема, Решение, Результат и Технологии.
          </p>
          <Link to="/dashboard/projects/new" className="btn btn-primary">
            Создать проект
          </Link>
        </div>
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
