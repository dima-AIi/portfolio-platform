"""Regression tests for the final audit fixes.

Each test here pins a defect that was confirmed at runtime before being fixed.
"""

import pytest

from app.core.security import hash_password
from app.utils.errors import AppError
from app.utils.password_strength import (
    BCRYPT_MAX_BYTES,
    validate_password_length,
    validate_password_strength,
)
from app.utils.rate_limit import _client_ip
from app.utils.slug import is_valid_username


class _FakeRequest:
    """Minimal stand-in exposing only what _client_ip reads."""

    def __init__(self, forwarded: str | None, peer: str = "10.0.0.1") -> None:
        self.headers = {} if forwarded is None else {"x-forwarded-for": forwarded}
        self.client = type("C", (), {"host": peer})()


class TestPasswordLength:
    """bcrypt refuses more than 72 bytes; the API used to return a 500."""

    def test_validate_password_length_accepts_exactly_the_limit(self):
        assert validate_password_length("a" * BCRYPT_MAX_BYTES)

    def test_validate_password_length_rejects_over_the_limit(self):
        with pytest.raises(ValueError, match="72"):
            validate_password_length("a" * (BCRYPT_MAX_BYTES + 1))

    def test_length_is_measured_in_bytes_not_characters(self):
        """Cyrillic is 2 bytes per character, so 40 of them already overflow."""
        with pytest.raises(ValueError):
            validate_password_length("П" * 40)

    def test_hash_password_raises_app_error_not_value_error(self):
        """A caller that bypasses the schema must not see a raw bcrypt crash."""
        with pytest.raises(AppError) as exc:
            hash_password("x" * (BCRYPT_MAX_BYTES + 1))
        assert exc.value.code == "PASSWORD_TOO_LONG"
        assert exc.value.status_code == 422

    def test_cyrillic_password_of_valid_length_is_hashed(self):
        assert hash_password("Пароль-Надёжный-123!")

    def test_password_still_must_be_strong(self):
        with pytest.raises(ValueError):
            validate_password_strength("password")

    def test_register_with_overlong_password_returns_422_not_500(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "long@example.com",
                "username": "longpw",
                "password": "Aa1!" + "x" * 100,
            },
        )
        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_password_change_with_overlong_password_returns_422(self, client, auth_headers):
        response = client.put(
            "/api/v1/auth/password",
            headers=auth_headers,
            json={"current_password": "strongpass123", "new_password": "Aa1!" + "x" * 100},
        )
        assert response.status_code == 422, response.text

    def test_reset_confirm_with_overlong_password_returns_422(self, client):
        response = client.post(
            "/api/v1/auth/reset-confirm",
            json={
                "email": "owner@example.com",
                "code": "000000",
                "new_password": "Aa1!" + "x" * 100,
            },
        )
        assert response.status_code == 422, response.text

    def test_a_valid_long_password_still_registers_and_logs_in(self, client):
        """The limit must not reject legitimate strong passwords."""
        password = "Aa1!" + "x" * 60
        registered = client.post(
            "/api/v1/auth/register",
            json={"email": "big@example.com", "username": "bigpw", "password": password},
        )
        assert registered.status_code == 201, registered.text
        login = client.post(
            "/api/v1/auth/login", json={"email": "big@example.com", "password": password}
        )
        assert login.status_code == 200, login.text


class TestReservedUsernames:
    """Usernames must not shadow real SPA routes."""

    def test_forgot_password_route_is_reserved(self):
        assert not is_valid_username("forgot-password")
        assert not is_valid_username("forgot_password")

    def test_reserved_names_cover_every_top_level_spa_route(self):
        """Mirrors AppRoutes: each of these paths wins over /:username."""
        for name in ("login", "register", "forgot-password", "dashboard"):
            assert not is_valid_username(name), name

    def test_forgot_password_registration_is_rejected(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "fp@example.com",
                "username": "forgot-password",
                "password": "strongpass123",
            },
        )
        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "USERNAME_RESERVED"


class TestRateLimitClientIp:
    """A forged X-Forwarded-For must not hand out a fresh rate-limit bucket."""

    def test_uses_the_rightmost_forwarded_entry(self):
        # The trusted proxy appends the real address, so the last hop is
        # the one an attacker cannot control.
        assert _client_ip(_FakeRequest("1.2.3.4, 5.6.7.8", peer="10.0.0.1")) == "5.6.7.8"

    def test_single_forwarded_entry_is_used(self):
        assert _client_ip(_FakeRequest("9.9.9.9")) == "9.9.9.9"

    def test_falls_back_to_socket_peer_without_the_header(self):
        assert _client_ip(_FakeRequest(None, peer="203.0.113.7")) == "203.0.113.7"

    def test_blank_entries_are_ignored(self):
        assert _client_ip(_FakeRequest("  , 5.6.7.8 ,  ")) == "5.6.7.8"

    def test_forged_prefix_cannot_bypass_the_login_limiter(self, client):
        """Rotating the client-supplied prefix must not reset the counter."""
        codes = []
        for attempt in range(14):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "nobody@example.com", "password": "whatever123"},
                # Same real client (last hop), different forged prefix.
                headers={"X-Forwarded-For": f"10.0.0.{attempt}, 198.51.100.9"},
            )
            codes.append(response.status_code)

        assert 429 in codes, "rate limit was bypassed by rotating the header"
        assert codes[:10] == [401] * 10
