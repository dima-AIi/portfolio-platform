import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ProjectImages } from "../components/project/ProjectImages";
import { ProjectPreview } from "../components/project/ProjectPreview";
import { TechSelect } from "../components/project/TechSelect";
import { Button } from "../components/ui/Button";
import { Field, Input, Textarea } from "../components/ui/Field";
import { StatusBadge } from "../components/ui/StatusBadge";
import { useToast } from "../hooks/useToast";
import { ApiError } from "../services/api";
import { portfolioApi } from "../services/portfolio";
import { projectsApi } from "../services/projects";
import type { Project, ProjectPayload, Technology } from "../types";

function emptyDraft(): Project {
  const now = new Date().toISOString();
  return {
    id: "draft",
    title: "",
    slug: "",
    short_description: null,
    problem: null,
    solution: null,
    features: null,
    result: null,
    role: null,
    cover_image_url: null,
    github_url: null,
    live_url: null,
    status: "DRAFT",
    sort_order: 0,
    view_count: 0,
    created_at: now,
    updated_at: now,
    published_at: null,
    technologies: [],
    images: [],
  };
}

export function ProjectEditorPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { showSuccess, showError, toastNode } = useToast();

  const isNew = !projectId;
  const [project, setProject] = useState<Project | null>(isNew ? emptyDraft() : null);
  const [technologies, setTechnologies] = useState<Technology[]>([]);
  const [selectedTechIds, setSelectedTechIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validation, setValidation] = useState<Record<string, string>>({});
  const [tab, setTab] = useState<"edit" | "preview">("edit");

  useEffect(() => {
    portfolioApi
      .technologies()
      .then(setTechnologies)
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (isNew) return;
    projectsApi
      .get(projectId!)
      .then((data) => {
        setProject(data);
        setSelectedTechIds(data.technologies.map((t) => t.id));
      })
      .catch(() => setError("Проект не найден."))
      .finally(() => setLoading(false));
  }, [projectId, isNew]);

  const payload: ProjectPayload = useMemo(
    () => ({
      title: project?.title.trim() || "",
      short_description: project?.short_description || null,
      problem: project?.problem || null,
      solution: project?.solution || null,
      features: project?.features || null,
      result: project?.result || null,
      role: project?.role || null,
      github_url: project?.github_url || null,
      live_url: project?.live_url || null,
      cover_image_url: project?.cover_image_url || null,
    }),
    [project],
  );

  const setField = useCallback(
    <K extends keyof Project>(name: K, value: Project[K]) => {
      setProject((prev) => (prev ? { ...prev, [name]: value } : prev));
    },
    [],
  );

  const validate = (): boolean => {
    const errors: Record<string, string> = {};
    if (!payload.title) errors.title = "Название обязательно.";
    if (payload.github_url && !/^https?:\/\/.+/.test(payload.github_url)) {
      errors.github_url = "Должна быть ссылка, начинающаяся с http(s)://";
    }
    if (payload.live_url && !/^https?:\/\/.+/.test(payload.live_url)) {
      errors.live_url = "Должна быть ссылка, начинающаяся с http(s)://";
    }
    setValidation(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = async (): Promise<Project | null> => {
    if (!validate()) return null;
    setSaving(true);
    setError(null);
    try {
      if (isNew) {
        const created = await projectsApi.create(payload);
        const withTechs =
          selectedTechIds.length > 0
            ? await projectsApi.setTechnologies(created.id, selectedTechIds)
            : created;
        setProject(withTechs);
        showSuccess("Проект создан");
        // Keep the user on the editor with a real id in the URL.
        navigate(`/dashboard/projects/${created.id}`, { replace: true });
        return withTechs;
      }
      const updated = await projectsApi.update(projectId!, payload);
      setProject(updated);
      showSuccess("Проект сохранён");
      return updated;
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Не удалось сохранить проект.";
      setError(message);
      showError("Ошибка сохранения");
      return null;
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAndTech = async () => {
    const saved = await handleSave();
    if (!saved || isNew) return;
    try {
      const updated = await projectsApi.setTechnologies(saved.id, selectedTechIds);
      setProject(updated);
      showSuccess("Технологии обновлены");
    } catch (err) {
      showError(err instanceof ApiError ? err.message : "Не удалось обновить технологии");
    }
  };

  const handlePublishToggle = async () => {
    if (!project) return;
    setPublishing(true);
    try {
      const updated =
        project.status === "PUBLISHED"
          ? await projectsApi.unpublish(project.id)
          : await projectsApi.publish(project.id);
      setProject(updated);
      showSuccess(
        updated.status === "PUBLISHED"
          ? "Проект опубликован"
          : "Проект перемещён в черновики",
      );
    } catch (err) {
      showError(err instanceof ApiError ? err.message : "Действие не удалось");
    } finally {
      setPublishing(false);
    }
  };

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
      </div>
    );
  }

  if (!isNew && !project) {
    return <div className="error-banner">{error ?? "Проект не найден."}</div>;
  }

  return (
    <div className="page project-editor">
      <div className="page-header-row">
        <div>
          <div className="editor-title-row">
            <h1 className="page-title">{isNew ? "Новый проект" : "Редактирование проекта"}</h1>
            {project && !isNew && <StatusBadge status={project.status} />}
          </div>
          <p className="page-subtitle" style={{ marginBottom: 0 }}>
            Хороший кейс отвечает на вопросы: какая проблема? какое решение? какой результат?
          </p>
        </div>
        <div className="editor-header-actions">
          {project && !isNew && (
            <Button
              variant={project.status === "PUBLISHED" ? "secondary" : "primary"}
              onClick={handlePublishToggle}
              disabled={publishing || saving}
            >
              {publishing
                ? "Обработка…"
                : project.status === "PUBLISHED"
                  ? "Скрыть"
                  : "Опубликовать"}
            </Button>
          )}
          <Button onClick={handleSaveAndTech} disabled={saving || publishing}>
            {saving ? "Сохранение…" : "Сохранить"}
          </Button>
          <Link to="/dashboard/projects" className="btn btn-ghost">
            Закрыть
          </Link>
        </div>
      </div>

      <div className="editor-tabs">
        <button
          className={`editor-tab ${tab === "edit" ? "active" : ""}`}
          onClick={() => setTab("edit")}
        >
          Редактирование
        </button>
        <button
          className={`editor-tab ${tab === "preview" ? "active" : ""}`}
          onClick={() => setTab("preview")}
        >
          Предпросмотр
        </button>
      </div>

      {tab === "preview" && project ? (
        <ProjectPreview project={project} />
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void handleSave();
          }}
          noValidate
        >
          {error && <div className="error-banner">{error}</div>}

          <section className="card card-pad editor-section">
            <h3>Основное</h3>
            <Field label="Название проекта" error={validation.title}>
              <Input
                value={project?.title ?? ""}
                onChange={(e) => setField("title", e.target.value as Project["title"])}
                placeholder="Telegram CRM"
                maxLength={120}
                invalid={!!validation.title}
              />
            </Field>
            <Field label="Краткое описание" hint="одно предложение — показывается на карточке">
              <Input
                value={project?.short_description ?? ""}
                onChange={(e) => setField("short_description", e.target.value)}
                placeholder="CRM-система для бизнеса в Telegram."
                maxLength={300}
              />
            </Field>
          </section>

          <section className="card card-pad editor-section">
            <h3>Кейс</h3>
            <p className="field-hint editor-section-lead">
              Заполняйте по мере готовности — проект сохраняется как черновик и виден только
              вам. Публиковать можно любую часть: например, описать пока только проблему и
              решение, а результат добавить позже.
            </p>
            <Field label="Проблема" hint="что было не так и кому это мешало">
              <Textarea
                value={project?.problem ?? ""}
                onChange={(e) => setField("problem", e.target.value)}
                placeholder="Клиенты студии записывались по телефону. Администратор тратил по часу в день на сверку, а часть клиентов не дожидалась ответа и уходила."
                rows={4}
              />
            </Field>
            <Field label="Решение" hint="что именно вы сделали">
              <Textarea
                value={project?.solution ?? ""}
                onChange={(e) => setField("solution", e.target.value)}
                placeholder="Сделал онлайн-запись: клиент выбирает услугу, мастера и свободный слот. Пересечения исключает сервер, а не ручная сверка."
                rows={4}
              />
            </Field>
            <div className="form-grid">
              <Field label="Моя роль" hint="необязательно. чем занимались вы лично">
                <Input
                  value={project?.role ?? ""}
                  onChange={(e) => setField("role", e.target.value)}
                  placeholder="Full-Stack разработчик: проектирование, вёрстка, серверная логика"
                  maxLength={120}
                />
              </Field>
              <Field label="Результат" hint="что изменилось. числа работают лучше слов">
                <Textarea
                  value={project?.result ?? ""}
                  onChange={(e) => setField("result", e.target.value)}
                  placeholder="Запись занимает около минуты и не требует звонков. Пересечения исключены на уровне сервера."
                  rows={3}
                />
              </Field>
            </div>
            <Field
              label="Функции"
              hint="необязательно. одна функция — одна строка, в списке появятся точки-маркеры"
            >
              <Textarea
                value={project?.features ?? ""}
                onChange={(e) => setField("features", e.target.value)}
                placeholder={"Онлайн-запись за 8 шагов\nКаталог услуг с ценами и фильтрами\nЛичный кабинет с историей\nPWA с офлайн-оболочкой"}
                rows={4}
              />
            </Field>
          </section>

          <section className="card card-pad editor-section">
            <h3>Технологии</h3>
            <TechSelect
              technologies={technologies}
              selectedIds={selectedTechIds}
              onChange={setSelectedTechIds}
            />
            <p className="field-hint">
              Нажмите «Сохранить», чтобы применить выбранные технологии к проекту.
            </p>
          </section>

          <section className="card card-pad editor-section">
            <h3>Ссылки</h3>
            <div className="form-grid">
              <Field label="Live Demo (работающий проект)" error={validation.live_url}>
                <Input
                  type="url"
                  value={project?.live_url ?? ""}
                  onChange={(e) => setField("live_url", e.target.value)}
                  placeholder="https://myproject.example.com"
                  invalid={!!validation.live_url}
                />
              </Field>
              <Field label="Ссылка на исходный код" error={validation.github_url}>
                <Input
                  type="url"
                  value={project?.github_url ?? ""}
                  onChange={(e) => setField("github_url", e.target.value)}
                  placeholder="https://github.com/username/project"
                  invalid={!!validation.github_url}
                />
              </Field>
            </div>
          </section>

          {!isNew && project && (
            <ProjectImages
              project={project}
              onProjectChange={setProject}
              onError={(msg) => showError(msg)}
            />
          )}

          <div className="form-actions editor-footer">
            <Button type="submit" size="lg" disabled={saving}>
              {saving ? "Сохранение…" : isNew ? "Создать проект" : "Сохранить изменения"}
            </Button>
            {isNew ? (
              <span className="field-hint">
                Проект появится в списке после нажатия «Создать проект».
              </span>
            ) : (
              project && (
                <span className="field-hint">
                  {project.status === "PUBLISHED"
                    ? "Проект виден на вашей публичной странице."
                    : "Черновик — виден только вам, пока не опубликуете."}
                </span>
              )
            )}
          </div>
        </form>
      )}
      {toastNode}
    </div>
  );
}
