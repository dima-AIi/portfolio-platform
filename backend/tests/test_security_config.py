"""Guards that the app cannot start with a publicly known signing key, plus
the cover/title validation that keeps a bad value from white-screening the
public project page."""

import pytest
from pydantic import ValidationError

from app.core.config import PLACEHOLDER_JWT_SECRET, Settings
from tests.conftest import create_project


class TestJwtSecretGuard:
    def test_production_refuses_the_placeholder_secret(self):
        """ENV defaults to production, so a forgotten JWT_SECRET must not boot.

        With the shipped placeholder anyone can sign a session cookie for any
        user id and take the account over.
        """
        with pytest.raises(ValidationError, match="JWT_SECRET"):
            Settings(ENV="production", JWT_SECRET=PLACEHOLDER_JWT_SECRET)

    def test_production_accepts_a_real_secret(self):
        assert Settings(ENV="production", JWT_SECRET="a" * 64).ENV == "production"

    def test_development_is_unaffected(self):
        """Local work must keep working with the example .env untouched."""
        settings = Settings(ENV="development", JWT_SECRET=PLACEHOLDER_JWT_SECRET)
        assert settings.JWT_SECRET == PLACEHOLDER_JWT_SECRET

    def test_env_defaults_to_production(self):
        """The default is the refuse state, not development."""
        assert Settings.model_fields["ENV"].default == "production"


class TestProjectCover:
    def test_cover_rejects_a_malformed_absolute_url(self, client, auth_headers):
        """'http://' is the payload that used to white-screen the public page.

        The frontend resolves the cover with new URL() to build the OG image;
        a throw there unmounts the whole page for every visitor.
        """
        response = client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={"title": "Битая обложка", "cover_image_url": "http://"},
        )
        assert response.status_code == 422, response.text

    def test_cover_rejects_a_script_url(self, client, auth_headers):
        response = client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={"title": "Скрипт", "cover_image_url": "javascript:alert(1)"},
        )
        assert response.status_code == 422

    def test_cover_still_accepts_a_repo_hosted_asset(self, client, auth_headers):
        """The showcase cover is an absolute https URL to committed static."""
        response = client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={
                "title": "Витрина",
                "cover_image_url": "https://site.example.com/dmitry/elora/og-cover.jpg",
            },
        )
        assert response.status_code == 201, response.text
        assert response.json()["cover_image_url"].startswith("https://site.example.com/")

    def test_cover_still_accepts_a_local_upload_path(self, client, auth_headers):
        response = client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={"title": "Загрузка", "cover_image_url": "/uploads/abc.jpg"},
        )
        assert response.status_code == 201, response.text

    def test_update_rejects_a_malformed_cover(self, client, auth_headers):
        project = create_project(client, auth_headers, title="Обновление обложки")
        response = client.put(
            f"/api/v1/projects/{project['id']}",
            headers=auth_headers,
            json={"cover_image_url": "not a url at all"},
        )
        assert response.status_code == 422


class TestProjectTitle:
    def test_update_rejects_an_empty_title(self, client, auth_headers):
        """ProjectUpdate redeclared title and silently lost min_length=1."""
        project = create_project(client, auth_headers, title="Нормальный")
        response = client.put(
            f"/api/v1/projects/{project['id']}",
            headers=auth_headers,
            json={"title": ""},
        )
        assert response.status_code == 422
