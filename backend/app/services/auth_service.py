import secrets
from datetime import timedelta

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db, utcnow
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    ResetRequestResponse,
    TokenResponse,
    UserResponse,
)
from app.services.email_service import send_password_reset_email
from app.utils.errors import AppError
from app.utils.images import delete_image_file

ALREADY_EXISTS_STATUS = 409
GENERIC_RESET_DETAIL = "Если аккаунт с таким email существует, код подтверждения отправлен."


class AuthService:
    def __init__(self, db: Session = Depends(get_db)):
        self.repo = UserRepository(db)
        self.resets = PasswordResetRepository(db)

    def register(self, data: RegisterRequest) -> TokenResponse:
        from app.utils.slug import is_valid_username

        if not is_valid_username(data.username):
            raise AppError("USERNAME_RESERVED", "Этот username зарезервирован системой. Выберите другой.", 422)
        if self.repo.get_by_email(data.email):
            raise AppError("EMAIL_ALREADY_EXISTS", "Этот email уже зарегистрирован.", ALREADY_EXISTS_STATUS)
        if self.repo.get_by_username(data.username):
            raise AppError("USERNAME_ALREADY_EXISTS", "Этот username уже занят.", ALREADY_EXISTS_STATUS)
        user = self.repo.create(data.email, data.username, hash_password(data.password))
        return self._token_response(user)

    def login(self, data: LoginRequest) -> TokenResponse:
        user = self.repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise AppError("INVALID_CREDENTIALS", "Неверный email или пароль.", 401)
        return self._token_response(user)

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.password_hash):
            raise AppError("INVALID_CREDENTIALS", "Текущий пароль указан неверно.", 400)
        user.password_hash = hash_password(new_password)
        self.repo.save(user)

    def change_email(self, user: User, email: str, password: str) -> UserResponse:
        if not verify_password(password, user.password_hash):
            raise AppError("INVALID_CREDENTIALS", "Текущий пароль указан неверно.", 400)
        email = email.lower()
        if email != user.email and self.repo.get_by_email(email):
            raise AppError("EMAIL_ALREADY_EXISTS", "Этот email уже зарегистрирован.", ALREADY_EXISTS_STATUS)
        user.email = email
        self.repo.save(user)
        return UserResponse.model_validate(user)

    def delete_account(self, user: User, password: str) -> None:
        if not verify_password(password, user.password_hash):
            raise AppError("INVALID_CREDENTIALS", "Текущий пароль указан неверно.", 400)
        # Collect upload paths before the delete: the DB cascade removes the
        # rows, but the files on disk would be left behind forever.
        urls: list[str] = []
        if user.profile and user.profile.avatar_url:
            urls.append(user.profile.avatar_url)
        for project in user.projects:
            urls.extend(image.url for image in project.images)
            if project.cover_image_url:
                urls.append(project.cover_image_url)
        self.repo.delete(user)
        for url in dict.fromkeys(urls):
            delete_image_file(url)

    def request_password_reset(self, email: str) -> ResetRequestResponse:
        user = self.repo.get_by_email(email)
        if not user:
            # Same response as success — do not leak which emails are registered.
            return ResetRequestResponse(detail=GENERIC_RESET_DETAIL)

        code = f"{secrets.randbelow(1_000_000):06d}"
        self.resets.invalidate_all(user.id)
        expires_at = utcnow() + timedelta(minutes=settings.PASSWORD_RESET_TTL_MINUTES)
        self.resets.create(user.id, hash_password(code), expires_at)

        if settings.smtp_enabled:
            try:
                send_password_reset_email(user.email, code)
            except Exception as exc:
                raise AppError(
                    "EMAIL_SEND_FAILED",
                    "Не удалось отправить письмо. Попробуйте позже.",
                    502,
                ) from exc
            return ResetRequestResponse(detail=GENERIC_RESET_DETAIL)

        if settings.ENV != "development":
            raise AppError(
                "EMAIL_NOT_CONFIGURED",
                "Почтовый сервис не настроен.",
                500,
            )
        # Development convenience: no SMTP configured -> surface the code in the
        # response so the flow is testable without a mail server.
        return ResetRequestResponse(detail=GENERIC_RESET_DETAIL, dev_code=code)

    def confirm_password_reset(self, email: str, code: str, new_password: str) -> None:
        user = self.repo.get_by_email(email)
        if not user:
            raise AppError("INVALID_RESET_CODE", "Неверный код подтверждения.", 400)
        reset = self.resets.get_latest_active(user.id, utcnow())
        if not reset or not verify_password(code, reset.code_hash):
            raise AppError("INVALID_RESET_CODE", "Неверный код подтверждения.", 400)
        reset.used = True
        user.password_hash = hash_password(new_password)
        self.repo.save(user)

    def _token_response(self, user: User) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user.id),
            user=UserResponse.model_validate(user),
        )
