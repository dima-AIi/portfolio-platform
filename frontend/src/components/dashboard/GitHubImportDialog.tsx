import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "../ui/Button";
import { ApiError } from "../../services/api";
import { githubApi, type GitHubRepo } from "../../services/ownerData";
import { plural } from "../../utils/plural";

/**
 * Lets the owner pull their own public GitHub repos and open them as drafts.
 *
 * Importing is deliberately not automatic: every repo becomes a draft that the
 * owner has to publish, so a fork or a throwaway experiment never shows up on
 * a public page by accident.
 */
export function GitHubImportDialog({ onClose }: { onClose: () => void }) {
  const [username, setUsername] = useState("");
  const [repos, setRepos] = useState<GitHubRepo[] | null>(null);
  const [chosen, setChosen] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const load = async () => {
    if (!username.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const { repos: found } = await githubApi.repos(username);
      setRepos(found);
      // Stars are a rough proxy for "worth showing", so they seed the selection.
      setChosen(new Set(found.filter((r) => r.stars > 0).slice(0, 5).map((r) => r.name)));
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось получить данные из GitHub. Попробуйте позже.",
      );
      setRepos(null);
    } finally {
      setLoading(false);
    }
  };

  const toggle = (name: string) => {
    setChosen((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal modal-wide"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Импорт из GitHub"
      >
        <h3>Импорт проектов из GitHub</h3>
        <p>
          Найдите свои публичные репозитории и превратите их в кейсы. Каждый проект
          создаётся как черновик — публиковать вы будете сами.
        </p>

        <div className="github-search">
          <input
            className="input"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Имя пользователя GitHub"
            onKeyDown={(e) => {
              if (e.key === "Enter") void load();
            }}
          />
          <Button type="button" onClick={() => void load()} disabled={loading || !username.trim()}>
            {loading ? "Ищем…" : "Найти"}
          </Button>
        </div>

        {error && <div className="error-banner">{error}</div>}

        {repos && repos.length === 0 && (
          <p className="muted">У этого пользователя нет публичных репозиториев.</p>
        )}

        {repos && repos.length > 0 && (
          <>
            <p className="muted">
              Найдено {repos.length}{" "}
              {plural(repos.length, "репозиторий", "репозитория", "репозиториев")}. Отметьте
              те, которые стоит показать.
            </p>
            <ul className="repo-list">
              {repos.map((repo) => (
                <li key={repo.name}>
                  <label>
                    <input
                      type="checkbox"
                      checked={chosen.has(repo.name)}
                      onChange={() => toggle(repo.name)}
                    />
                    <span className="repo-main">
                      <strong>{repo.name}</strong>
                      {repo.description && (
                        <span className="muted">{repo.description}</span>
                      )}
                      <span className="repo-meta">
                        {repo.language && <span>{repo.language}</span>}
                        {repo.stars > 0 && <span>★ {repo.stars}</span>}
                        {repo.archived && <span>архивный</span>}
                      </span>
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          </>
        )}

        <div className="modal-actions">
          <Button variant="secondary" onClick={onClose}>
            Закрыть
          </Button>
          {repos && chosen.size > 0 && (
            <Button
              onClick={() => {
                onClose();
                navigate("/dashboard/projects/new", {
                  state: { githubRepos: repos.filter((r) => chosen.has(r.name)) },
                });
              }}
            >
              Создать {chosen.size}{" "}
              {plural(chosen.size, "проект", "проекта", "проектов")}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
