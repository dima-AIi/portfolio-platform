import os
import uuid

from fastapi import UploadFile

from app.core.config import settings
from app.utils.errors import AppError
from app.utils.slug import random_filename

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def has_valid_signature(content: bytes, extension: str) -> bool:
    """Magic-bytes check: the real file format must match the declared one."""
    if extension == ".png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if extension == ".jpg":
        return content.startswith(b"\xff\xd8\xff")
    if extension == ".webp":
        return content[:4] == b"RIFF" and content[8:12] == b"WEBP"
    return False


def uploads_dir() -> str:
    path = settings.UPLOAD_DIR
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), path)
    os.makedirs(path, exist_ok=True)
    return path


def validate_image(file: UploadFile) -> None:
    if (file.content_type or "") not in ALLOWED_IMAGE_TYPES:
        raise AppError("INVALID_IMAGE", "Поддерживаются только изображения JPEG, PNG или WebP.", 400)
    if file.size is not None and file.size > settings.max_upload_size_bytes:
        raise AppError(
            "FILE_TOO_LARGE",
            f"Файл превышает максимальный размер {settings.MAX_UPLOAD_SIZE_MB} МБ.",
            413,
        )


async def save_image(file: UploadFile) -> str:
    """Validate and save an uploaded image. Returns public URL path."""
    validate_image(file)
    extension = ALLOWED_IMAGE_TYPES[file.content_type]
    contents = await file.read()
    if len(contents) > settings.max_upload_size_bytes:
        raise AppError(
            "FILE_TOO_LARGE",
            f"Файл превышает максимальный размер {settings.MAX_UPLOAD_SIZE_MB} МБ.",
            413,
        )
    if not has_valid_signature(contents, extension):
        raise AppError(
            "INVALID_IMAGE",
            "Содержимое файла не соответствует заявленному формату изображения.",
            400,
        )
    filename = random_filename(extension)
    path = os.path.join(uploads_dir(), filename)
    with open(path, "wb") as f:
        f.write(contents)
    return f"/uploads/{filename}"


def delete_image_file(url: str) -> None:
    if not url.startswith("/uploads/"):
        return
    path = os.path.join(uploads_dir(), os.path.basename(url))
    if os.path.isfile(path):
        os.remove(path)


def new_uuid() -> str:
    return str(uuid.uuid4())
