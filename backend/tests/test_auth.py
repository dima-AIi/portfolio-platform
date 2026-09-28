import uuid

from app.core.security import SESSION_COOKIE_NAME
from tests.conftest import _token_from_cookie


def session_token(response) -> str:
    return _token_from_cookie(response)


class TestRegister:
    def test_register_success(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "a@example.com", "username": "usera", "password": "strongpass123"},
        )
        assert response.status_code == 201
        data = response.json()
        # The JWT must not be in the body — it travels in an httpOnly cookie.
        assert "access_token" not in data
        assert data["user"]["email"] == "a@example.com"
        assert data["user"]["username"] == "usera"
        assert "password" not in data["user"]

    def test_register_sets_httponly_session_cookie(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "cookie@example.com", "username": "cookieuser", "password": "strongpass123"},
        )
        cookie_header = response.headers["set-cookie"]
        assert SESSION_COOKIE_NAME in cookie_header
        assert "HttpOnly" in cookie_header
        assert "SameSite=lax" in cookie_header.replace("samesite", "SameSite")

    def test_session_cookie_authenticates_requests(self, logged_in_client):
        """The browser path: a cookie alone must be enough, no header needed."""
        assert logged_in_client.get("/api/v1/auth/me").status_code == 200
        assert logged_in_client.get("/api/v1/projects").status_code == 200

    def test_bearer_header_still_works_for_api_clients(self, client, auth_headers):
        assert client.get("/api/v1/auth/me", headers=auth_headers).status_code == 200

    def test_bearer_header_overrides_the_session_cookie(self, client, auth_headers, second_user_headers):
        """A browser sends its cookie automatically, so an explicit
        Authorization header must still be able to act as another identity.

        Note the client currently holds `other`'s cookie — it was the last
        registration to touch the cookie jar.
        """
        assert client.get("/api/v1/auth/me").json()["username"] == "other"

        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.json()["username"] == "owner"

    def test_logout_clears_session_cookie(self, logged_in_client):
        assert logged_in_client.get("/api/v1/auth/me").status_code == 200
        response = logged_in_client.post("/api/v1/auth/logout")
        assert response.status_code == 204
        assert SESSION_COOKIE_NAME in response.headers["set-cookie"]
        assert logged_in_client.get("/api/v1/auth/me").status_code == 401

    def test_no_credentials_rejected(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_tampered_cookie_rejected(self, logged_in_client):
        logged_in_client.cookies.set(SESSION_COOKIE_NAME, "not.a.jwt")
        assert logged_in_client.get("/api/v1/auth/me").status_code == 401

    def test_register_duplicate_email(self, client):
        payload = {"email": "dup@example.com", "username": "user1", "password": "strongpass123"}
        client.post("/api/v1/auth/register", json=payload)
        payload["username"] = "user2"
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"

    def test_register_duplicate_username(self, client):
        client.post(
            "/api/v1/auth/register",
            json={"email": "one@example.com", "username": "same", "password": "strongpass123"},
        )
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "two@example.com", "username": "same", "password": "strongpass123"},
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "USERNAME_ALREADY_EXISTS"

    def test_register_invalid_username(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "x@example.com", "username": "Bad Username", "password": "strongpass123"},
        )
        assert response.status_code == 422

    def test_register_reserved_username(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "x@example.com", "username": "admin", "password": "strongpass123"},
        )
        assert response.status_code == 422

    def test_register_short_password(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "x@example.com", "username": "userx", "password": "short"},
        )
        assert response.status_code == 422

    def test_register_creates_profile(self, client, auth_headers):
        response = client.get("/api/v1/profile", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["display_name"] is None


class TestLogin:
    def test_login_success(self, client, auth_headers):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "owner@example.com", "password": "strongpass123"},
        )
        assert response.status_code == 200
        assert "access_token" not in response.json()
        assert bool(session_token(response))

    def test_login_wrong_password(self, client, auth_headers):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "owner@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_login_unknown_email(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "whatever123"},
        )
        assert response.status_code == 401

    def test_me_requires_auth(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_me_with_token(self, client, auth_headers):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["username"] == "owner"

    def test_me_with_invalid_token(self, client):
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {uuid.uuid4().hex}"}
        )
        assert response.status_code == 401


class TestRateLimit:
    def test_login_rate_limited(self, client):
        for _ in range(10):
            client.post(
                "/api/v1/auth/login",
                json={"email": "ghost@example.com", "password": "whatever123"},
            )
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "whatever123"},
        )
        assert response.status_code == 429
        assert response.json()["error"]["code"] == "RATE_LIMITED"

    def test_register_rate_limited(self, client):
        for i in range(5):
            client.post(
                "/api/v1/auth/register",
                json={"email": f"u{i}@example.com", "username": f"user{i}", "password": "strongpass123"},
            )
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "u99@example.com", "username": "user99", "password": "strongpass123"},
        )
        assert response.status_code == 429

    def test_rate_limit_does_not_affect_other_endpoints(self, client, auth_headers):
        for _ in range(10):
            client.post(
                "/api/v1/auth/login",
                json={"email": "ghost@example.com", "password": "whatever123"},
            )
        assert client.get("/api/v1/projects", headers=auth_headers).status_code == 200


class TestPasswordStrength:
    def test_register_common_password_rejected(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "weak@example.com", "username": "weakuser", "password": "password"},
        )
        assert response.status_code == 422
        assert "распростран" in response.json()["error"]["message"]

    def test_register_digits_only_rejected(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "weak@example.com", "username": "weakuser", "password": "12345678"},
        )
        assert response.status_code == 422

    def test_register_letters_only_rejected(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "weak@example.com", "username": "weakuser", "password": "abcdefghij"},
        )
        assert response.status_code == 422

    def test_register_mixed_password_ok(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "ok@example.com", "username": "okuser", "password": "m1xed-pa55w0rd"},
        )
        assert response.status_code == 201

    def test_change_to_weak_password_rejected(self, client, auth_headers):
        response = client.put(
            "/api/v1/auth/password",
            headers=auth_headers,
            json={"current_password": "strongpass123", "new_password": "qwerty123"},
        )
        assert response.status_code == 422


class TestPasswordChange:
    def test_change_password(self, client, auth_headers):
        response = client.put(
            "/api/v1/auth/password",
            headers=auth_headers,
            json={"current_password": "strongpass123", "new_password": "newpass12345"},
        )
        assert response.status_code == 204
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "owner@example.com", "password": "newpass12345"},
        )
        assert response.status_code == 200

    def test_change_password_wrong_current(self, client, auth_headers):
        response = client.put(
            "/api/v1/auth/password",
            headers=auth_headers,
            json={"current_password": "wrongpass", "new_password": "newpass12345"},
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_change_password_short_new(self, client, auth_headers):
        response = client.put(
            "/api/v1/auth/password",
            headers=auth_headers,
            json={"current_password": "strongpass123", "new_password": "short"},
        )
        assert response.status_code == 422

    def test_change_password_requires_auth(self, client):
        response = client.put(
            "/api/v1/auth/password",
            json={"current_password": "a12345678", "new_password": "b12345678"},
        )
        assert response.status_code == 401
