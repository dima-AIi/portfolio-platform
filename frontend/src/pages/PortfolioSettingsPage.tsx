import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useToast } from "../hooks/useToast";
import { useAuth } from "../hooks/useAuth";
import { CopyLinkButton } from "../components/ui/CopyLinkButton";
import { profileApi } from "../services/profile";
import { projectsApi } from "../services/projects";
import type { Profile, Project } from "../types";

const THEMES = [
  { id: "classic", name: "Классическая", desc: "Светлая, с карточками" },
  { id: "dark", name: "Тёмная", desc: "Для разработчиков" },
  { id: "minimal", name: "Минимал", desc: "Максимум воздуха" },
];

export function PortfolioSettingsPage() {
  const { user } = useAuth();
  const { showSuccess, showError, toastNode } = useToast();
  const [projects, setProjects] = useState<Project[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [savingTheme, setSavingTheme] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([projectsApi.list(), profileApi.get()])
      .then(([data, prof]) => {
        setProjects(data.items);
        setProfile(prof);
      })
      .finally(() => setLoading(false));
  }, []);

  const chooseTheme = async (theme: string) => {
    if (!profile || profile.theme === theme) return;
    setSavingTheme(theme);
    try {
      const updated = await profileApi.update({ theme } as Partial<Profile>);
      setProfile(updated);
      showSuccess("Тема обновлена");
    } catch {
      showError("Не удалось сохранить тему");
    } finally {
      setSavingTheme(null);
    }
  };

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
      </div>
    );
  }

  const published = projects.filter((p) => p.status === "PUBLISHED");

  return (
    <div className="page">
      <h1 className="page-title">Портфолио</h1>
      <p className="page-subtitle">
        Всё, что вы публикуете здесь, становится видно на публичной странице.
      </p>

      <div className="card card-pad portfolio-summary">
        <div>
          <h3>Ваша публичная ссылка</h3>
          <p className="muted">
            <strong>{user ? `/${user.username}` : ""}</strong>
            {published.length === 0 &&
              " — опубликуйте хотя бы один проект, чтобы страница была интересной."}
          </p>
        </div>
        {user && (
          <div className="share-actions">
            <CopyLinkButton to={`/${user.username}`} />
            <Link to={`/${user.username}`} className="btn btn-primary">
              Открыть публичную страницу ↗
            </Link>
          </div>
        )}
      </div>

      <h3 style={{ margin: "32px 0 12px" }}>Оформление страницы</h3>
      <div className="theme-grid">
        {THEMES.map((theme) => (
          <button
            key={theme.id}
            type="button"
            className={`theme-option ${profile?.theme === theme.id ? "selected" : ""}`}
            onClick={() => void chooseTheme(theme.id)}
            disabled={savingTheme !== null}
          >
            <span className={`theme-preview theme-preview-${theme.id}`}>
              <span className="theme-preview-avatar" />
              <span className="theme-preview-line" />
              <span className="theme-preview-line short" />
            </span>
            <strong>{theme.name}</strong>
            <span className="muted">{theme.desc}</span>
            {profile?.theme === theme.id && <span className="theme-check">✓ выбрана</span>}
          </button>
        ))}
      </div>

      <h3 style={{ margin: "32px 0 12px" }}>Опубликовано на странице ({published.length})</h3>
      {published.length === 0 ? (
        <p className="muted">
          Пока ничего не опубликовано.{" "}
          <Link to="/dashboard/projects">Перейти к проектам →</Link>
        </p>
      ) : (
        <ul className="published-list">
          {published.map((p) => (
            <li key={p.id}>
              <div className="published-list-main">
                <span>{p.title}</span>
                <span className="muted">
                  /{user?.username}/projects/{p.slug}
                </span>
              </div>
              <CopyLinkButton
                to={`/${user?.username}/projects/${p.slug}`}
                label="Скопировать"
              />
            </li>
          ))}
        </ul>
      )}
      {toastNode}
    </div>
  );
}
