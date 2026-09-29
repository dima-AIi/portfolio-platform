from tests.conftest import create_project


class TestViewCounts:
    def test_portfolio_view_increments(self, client, auth_headers):
        project = create_project(client, auth_headers, title="Viewed")
        client.post(f"/api/v1/projects/{project['id']}/publish", headers=auth_headers)

        first = client.get("/api/v1/public/owner").json()["profile"]["view_count"]
        second = client.get("/api/v1/public/owner").json()["profile"]["view_count"]
        assert second == first + 1

    def test_project_view_increments(self, client, auth_headers):
        project = create_project(client, auth_headers, title="Viewed Project")
        client.post(f"/api/v1/projects/{project['id']}/publish", headers=auth_headers)

        first = client.get("/api/v1/public/owner/projects/viewed-project").json()
        second = client.get("/api/v1/public/owner/projects/viewed-project").json()
        assert second["project"]["view_count"] == first["project"]["view_count"] + 1

    def test_draft_view_not_counted(self, client, auth_headers):
        create_project(client, auth_headers, title="Invisible")
        assert client.get("/api/v1/public/owner/projects/invisible").status_code == 404
        profile = client.get("/api/v1/public/owner").json()["profile"]
        assert profile["view_count"] == 1  # only this portfolio request counted

    def test_owner_sees_counts_in_dashboard(self, client, auth_headers):
        project = create_project(client, auth_headers, title="Counted")
        client.post(f"/api/v1/projects/{project['id']}/publish", headers=auth_headers)
        client.get("/api/v1/public/owner")
        client.get("/api/v1/public/owner/projects/counted")

        listing = client.get("/api/v1/projects", headers=auth_headers).json()
        assert listing["items"][0]["view_count"] == 1
        profile = client.get("/api/v1/profile", headers=auth_headers).json()
        assert profile["view_count"] == 1


class TestEmailChange:
    def test_change_email(self, client, auth_headers):
        response = client.put(
            "/api/v1/auth/email",
            headers=auth_headers,
            json={"email": "newowner@example.com", "password": "strongpass123"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == "newowner@example.com"
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "newowner@example.com", "password": "strongpass123"},
        )
        assert response.status_code == 200

    def test_change_email_wrong_password(self, client, auth_headers):
        response = client.put(
            "/api/v1/auth/email",
            headers=auth_headers,
            json={"email": "newowner@example.com", "password": "wrong"},
        )
        assert response.status_code == 400

    def test_change_email_taken(self, client, auth_headers, second_user_headers):
        response = client.put(
            "/api/v1/auth/email",
            headers=auth_headers,
            json={"email": "other@example.com", "password": "strongpass123"},
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


class TestAccountDeletion:
    def test_delete_account_removes_everything(self, client, auth_headers):
        project = create_project(client, auth_headers, title="Doomed")
        client.post(f"/api/v1/projects/{project['id']}/publish", headers=auth_headers)
        assert client.get("/api/v1/public/owner").status_code == 200

        response = client.request(
            "DELETE",
            "/api/v1/auth/account",
            headers=auth_headers,
            json={"password": "strongpass123"},
        )
        assert response.status_code == 204

        assert client.get("/api/v1/public/owner").status_code == 404
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "owner@example.com", "password": "strongpass123"},
        )
        assert login.status_code == 401

    def test_delete_account_wrong_password(self, client, auth_headers):
        response = client.request(
            "DELETE", "/api/v1/auth/account", headers=auth_headers, json={"password": "wrong"}
        )
        assert response.status_code == 400

    def test_username_freed_after_deletion(self, client, auth_headers):
        client.request(
            "DELETE",
            "/api/v1/auth/account",
            headers=auth_headers,
            json={"password": "strongpass123"},
        )
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "fresh@example.com", "username": "owner", "password": "strongpass123"},
        )
        assert response.status_code == 201

    def test_delete_account_removes_analytics_rows(self, client, auth_headers):
        """page_views has no ORM cascade, so it used to outlive the account."""
        from app.core.database import SessionLocal
        from app.models import PageView

        project = create_project(client, auth_headers, title="Tracked")
        client.post(f"/api/v1/projects/{project['id']}/publish", headers=auth_headers)
        client.get("/api/v1/public/owner")
        client.get("/api/v1/public/owner/projects/tracked")

        db = SessionLocal()
        assert db.query(PageView).count() == 2
        db.close()

        response = client.request(
            "DELETE",
            "/api/v1/auth/account",
            headers=auth_headers,
            json={"password": "strongpass123"},
        )
        assert response.status_code == 204

        db = SessionLocal()
        assert db.query(PageView).count() == 0, "analytics rows survived deletion"
        db.close()

