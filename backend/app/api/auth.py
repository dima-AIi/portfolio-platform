import uuid

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    SESSION_COOKIE_NAME,
    clear_session_cookie,
    decode_access_token,
    set_session_cookie,
)
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AccountDeleteRequest,
    EmailChangeRequest,
    LoginRequest,
    PasswordChangeRequest,
    RegisterRequest,
    ResetConfirm,
    ResetRequest,
    ResetRequestResponse,
    SessionResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.utils.rate_limit import rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])

register_limit = rate_limit(max_requests=5, window_seconds=60, path_max=60)
login_limit = rate_limit(max_requests=10, window_seconds=60, path_max=300)
reset_request_limit = rate_limit(max_requests=3, window_seconds=60, path_max=30)
reset_confirm_limit = rate_limit(max_requests=10, window_seconds=60, path_max=100)

bearer_scheme = HTTPBearer(auto_error=False)

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован"
)


def get_current_user(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the current user from the session cookie, falling back to a
    Bearer header.

    An explicit Authorization header wins over the cookie. A cookie is sent
    automatically by the browser, so giving it priority would let a cookie
    silently override the identity an API client asked for. The header is
    always a deliberate choice by the caller.
    """
    token = (credentials.credentials if credentials else None) or session_token
    if not token:
        raise CREDENTIALS_ERROR
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный или истёкший токен"
        )
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        # The token was signed by us but carries a non-UUID subject — treat it
        # as missing credentials rather than leaking the parse error.
        raise CREDENTIALS_ERROR from None
    user = UserRepository(db).get_by_id(user_uuid)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден"
        )
    return user


@router.post("/register", response_model=SessionResponse, status_code=201,
             dependencies=[Depends(register_limit)])
def register(
    data: RegisterRequest, response: Response, service: AuthService = Depends()
) -> SessionResponse:
    return _start_session(service.register(data), response)


@router.post("/login", response_model=SessionResponse,
             dependencies=[Depends(login_limit)])
def login(
    data: LoginRequest, response: Response, service: AuthService = Depends()
) -> SessionResponse:
    return _start_session(service.login(data), response)


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    """Drop the session cookie.

    The token itself is stateless, so the server cannot revoke it before it
    expires — the cookie is removed, which is what ends the browser session.
    """
    clear_session_cookie(response)


def _start_session(result, response: Response) -> SessionResponse:
    set_session_cookie(response, result.access_token)
    return SessionResponse(user=result.user)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/reset-request", response_model=ResetRequestResponse,
             dependencies=[Depends(reset_request_limit)])
def reset_request(
    data: ResetRequest, service: AuthService = Depends()
) -> ResetRequestResponse:
    return service.request_password_reset(data.email)


@router.post("/reset-confirm", status_code=204,
             dependencies=[Depends(reset_confirm_limit)])
def reset_confirm(data: ResetConfirm, service: AuthService = Depends()) -> None:
    service.confirm_password_reset(data.email, data.code, data.new_password)


@router.put("/password", status_code=204)
def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(),
) -> None:
    service.change_password(current_user, data.current_password, data.new_password)


@router.put("/email", response_model=UserResponse)
def change_email(
    data: EmailChangeRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(),
) -> UserResponse:
    return service.change_email(current_user, data.email, data.password)


@router.delete("/account", status_code=204)
def delete_account(
    data: AccountDeleteRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(),
) -> None:
    service.delete_account(current_user, data.password)
