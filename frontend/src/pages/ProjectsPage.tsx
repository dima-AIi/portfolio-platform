import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorBanner } from "../components/ui/ErrorBanner";
import { StatusBadge } from "../components/ui/StatusBadge";
import { Button } from "../components/ui/Button";
import { useToast } from "../hooks/useToast";
import { ApiError } from "../services/api";
import { projectsApi } from "../services/projects";
import type { Project } from "../types";

export function ProjectsPage() {
  const { showSuccess, showError, toastNode } = useToast();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<Project | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [dragIndex, setDragIndex] = useState<number | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    projectsApi
      .list()
      .then((data) => setProjects(data.items))
      .catch(() => setError("Не удалось загрузить проекты."))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const commitOrder = async (next: Project[]) => {
    setProjects(next);
    try {
      await projectsApi.reorder(next.map((p) => p.id));
    } catch {
      showError("Не удалось сохранить новый порядок");
      load();
    }
  };

  const move = async (index: number, direction: -1 | 1) => {
    const next = [...projects];
    const target = index + direction;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    await commitOrder(next);
  };

  const handleDrop = async (target: number) => {
    if (dragIndex === null || dragIndex === target) {
      setDragIndex(null);
      return;
    }
    const next = [...projects];
    const [moved] = next.splice(dragIndex, 1);
    next.splice(target, 0, moved);
    setDragIndex(null);
    await commitOrder(next);
  };

  const togglePublish = async (project: Project) => {
    setBusyId(project.id);
    try {
      const updated =
        project.status === "PUBLISHED"
          ? await projectsApi.unpublish(project.id)
          : await projectsApi.publish(project.id);
      setProjects((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
      showSuccess(
        updated.status === "PUBLISHED" ? "Проект опубликован" : "Проект скрыт в черновики",
      );
    } catch (err) {
      showError(err instanceof ApiError ? err.message : "Действие не удалось");
    } finally {
      setBusyId(null);
    }
  };

  const confirmDelete = async () => {
    if (!deleting) return;
    setBusyId(deleting.id);
    try {
      await projectsApi.remove(deleting.id);
      setProjects((prev) => prev.filter((p) => p.id !== deleting.id));
      showSuccess("Проект удалён");
    } catch {
      showError("Не удалось удалить проект");
    } finally {
      setBusyId(null);
      setDeleting(null);
    }
  };

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Проекты</h1>
          <p className="page-subtitle" style={{ marginBottom: 0 }}>
            Порядок в списке = порядок на публичной странице.
          </p>
        </div>
        <Link to="/dashboard/projects/new" className="btn btn-primary">
          + Новый проект
        </Link>
      </div>

      {error && <ErrorBanner message={error} onRetry={load} />}

      {projects.length === 0 && !error ? (
        <EmptyState
          title="Пока нет проектов"
          description="Добавьте первый проект в виде кейса: Проблема, Решение, Результат и Технологии."
          action={
            <Link to="/dashboard/projects/new" className="btn btn-primary">
              Создать первый проект
            </Link>
          }
        />
      ) : (
        <div className="project-list">
          {projects.map((project, index) => (
            <div
              key={project.id}
              className={`card project-row ${dragIndex === index ? "dragging" : ""}`}
              draggable
              onDragStart={(e) => {
                setDragIndex(index);
                e.dataTransfer.effectAllowed = "move";
              }}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => void handleDrop(index)}
              onDragEnd={() => setDragIndex(null)}
            >
              <span className="drag-handle" aria-hidden="true">
                ⠿
              </span>
              <div className="project-row-cover">
                {project.cover_image_url ? (
                  <img src={project.cover_image_url} alt="" />
                ) : (
                  <span className="project-row-cover-empty">Нет фото</span>
                )}
              </div>
              <div className="project-row-main">
                <div className="project-row-title">
                  <h3>{project.title}</h3>
                  <StatusBadge status={project.status} />
                  <span className="view-count" title="Просмотры на публичной странице">
                    👁 {project.view_count}
                  </span>
                </div>
                <p className="muted">{project.short_description || "Описание пока не заполнено."}</p>
                <div className="tech-row">
                  {project.technologies.slice(0, 5).map((t) => (
                    <span key={t.id} className="badge badge-tech">
                      {t.name}
                    </span>
                  ))}
                </div>
              </div>
              <div className="project-row-actions">
                <div className="reorder-controls">
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm btn-icon"
                    onClick={() => move(index, -1)}
                    disabled={index === 0}
                    aria-label="Переместить выше"
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm btn-icon"
                    onClick={() => move(index, 1)}
                    disabled={index === projects.length - 1}
                    aria-label="Переместить ниже"
                  >
                    ↓
                  </button>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => togglePublish(project)}
                  disabled={busyId === project.id}
                >
                  {project.status === "PUBLISHED" ? "Скрыть" : "Опубликовать"}
                </Button>
                <Link to={`/dashboard/projects/${project.id}`} className="btn btn-secondary btn-sm">
                  Редактировать
                </Link>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => setDeleting(project)}
                  disabled={busyId === project.id}
                >
                  Удалить
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!deleting}
        title={`Удалить «${deleting?.title ?? ""}»?`}
        description="Проект будет удалён безвозвратно вместе с изображениями и технологиями. Это действие нельзя отменить."
        confirmLabel="Удалить"
        onCancel={() => setDeleting(null)}
        onConfirm={confirmDelete}
      />
      {toastNode}
    </div>
  );
}
