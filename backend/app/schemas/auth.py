import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.utils.password_strength import (
    validate_password_length,
    validate_password_strength,
)


# Every user-supplied password goes through both checks, so bcrypt can never
# receive more than it is able to hash.
def _check_new_password(value: str) -> str:
    return validate_password_length(validate_password_strength(value))


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-z0-9][a-z0-9_-]{2,29}$")
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return _check_new_password(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return _check_new_password(value)


class EmailChangeRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AccountDeleteRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class ResetRequest(BaseModel):
    email: EmailStr


class ResetRequestResponse(BaseModel):
    detail: str
    dev_code: str | None = None


class ResetConfirm(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{6}$")
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return _check_new_password(value)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SessionResponse(BaseModel):
    """Returned to browser clients.

    Deliberately carries no token: the JWT travels in an httpOnly cookie so
    that script on the page cannot read it.
    """

    user: UserResponse
