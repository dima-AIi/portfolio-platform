import type { Project } from "../../types";
import { CaseText } from "./CaseText";

interface ProjectPreviewProps {
  project: Project;
}

export function ProjectPreview({ project }: ProjectPreviewProps) {
  return (
    <div className="preview-wrap">
      <article className="card preview-card">
        {project.cover_image_url && (
          <img src={project.cover_image_url} alt="" className="preview-cover" />
        )}
        <div className="preview-body">
          <h1>{project.title || "Проект без названия"}</h1>
          <p className="preview-lead">{project.short_description}</p>

          <div className="tech-row" style={{ marginBottom: 24 }}>
            {project.technologies.map((t) => (
              <span key={t.id} className="badge badge-tech">
                {t.name}
              </span>
            ))}
          </div>

          {/* Rendered through the same CaseText the public page uses, so the
              preview shows the real paragraph and list layout. */}
          {project.problem && (
            <section className="preview-section">
              <h4>Проблема</h4>
              <CaseText text={project.problem} />
            </section>
          )}
          {project.solution && (
            <section className="preview-section">
              <h4>Решение</h4>
              <CaseText text={project.solution} />
            </section>
          )}
          {project.role && (
            <section className="preview-section">
              <h4>Моя роль</h4>
              <p>{project.role}</p>
            </section>
          )}
          {project.features && (
            <section className="preview-section">
              <h4>Функции</h4>
              <CaseText text={project.features} linesAsList />
            </section>
          )}
          {project.result && (
            <section className="preview-section">
              <h4>Результат</h4>
              <CaseText text={project.result} />
            </section>
          )}

          <div className="preview-links">
            {project.live_url && (
              <a href={project.live_url} target="_blank" rel="noreferrer" className="btn btn-primary">
                Live demo ↗
              </a>
            )}
            {project.github_url && (
              <a
                href={project.github_url}
                target="_blank"
                rel="noreferrer"
                className="btn btn-secondary"
              >
                Исходный код ↗
              </a>
            )}
          </div>
        </div>
      </article>
    </div>
  );
}
