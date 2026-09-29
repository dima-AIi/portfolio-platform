import { useState } from "react";

import { ApiError } from "../../services/api";
import { projectsApi } from "../../services/projects";
import type { Project, ProjectImage } from "../../types";

interface ProjectImagesProps {
  project: Project;
  /**
   * Accepts an updater so a server response can patch just the field it
   * changed. Passing the whole returned project instead used to replace the
   * editor state with the last *saved* copy, silently discarding every
   * unsaved edit to the case text.
   */
  onProjectChange: (updater: (project: Project) => Project) => void;
  onError: (message: string) => void;
}

export function ProjectImages({ project, onProjectChange, onError }: ProjectImagesProps) {
  const [uploading, setUploading] = useState(false);
  const [busyImageId, setBusyImageId] = useState<string | null>(null);

  const upload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const image = await projectsApi.uploadImage(project.id, file);
      onProjectChange((prev) => ({ ...prev, images: [...prev.images, image] }));
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Не удалось загрузить изображение.");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  const setCover = async (image: ProjectImage) => {
    setBusyImageId(image.id);
    try {
      await projectsApi.update(project.id, { cover_image_url: image.url });
      // Patch only the cover: the local case text is still unsaved and must
      // survive this call.
      onProjectChange((prev) => ({ ...prev, cover_image_url: image.url }));
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Не удалось установить обложку.");
    } finally {
      setBusyImageId(null);
    }
  };

  const removeImage = async (image: ProjectImage) => {
    setBusyImageId(image.id);
    try {
      await projectsApi.deleteImage(project.id, image.id);
      onProjectChange((prev) => ({
        ...prev,
        images: prev.images.filter((img) => img.id !== image.id),
        cover_image_url: prev.cover_image_url === image.url ? null : prev.cover_image_url,
      }));
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Не удалось удалить изображение.");
    } finally {
      setBusyImageId(null);
    }
  };

  return (
    <section className="card card-pad editor-section">
      <h3>Обложка и изображения</h3>
      <p className="muted" style={{ marginBottom: 16 }}>
        Обложка показывается на карточке проекта в портфолио. JPEG, PNG или WebP до 5 МБ.
      </p>
      <label className="upload-dropzone">
        <input type="file" accept="image/jpeg,image/png,image/webp" onChange={upload} hidden />
        {uploading ? "Загрузка…" : "+ Добавить изображение"}
      </label>

      {project.images.length > 0 && (
        <div className="image-grid">
          {project.images.map((image) => {
            const busy = busyImageId === image.id;
            return (
              <div key={image.id} className="image-tile">
                <img src={image.url} alt="" />
                <div className="image-tile-actions">
                  {project.cover_image_url === image.url ? (
                    <span className="badge badge-published">Обложка</span>
                  ) : (
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => void setCover(image)}
                      disabled={busy}
                    >
                      Сделать обложкой
                    </button>
                  )}
                  <button
                    type="button"
                    className="btn btn-danger btn-sm"
                    onClick={() => void removeImage(image)}
                    disabled={busy}
                  >
                    Удалить
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
