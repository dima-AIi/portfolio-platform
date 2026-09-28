
from tests.conftest import create_project


def publish_project(client, headers, project):
    response = client.post(f"/api/v1/projects/{project['id']}/publish", headers=headers)
    assert response.status_code == 200
    return response.json()


class TestPublicPortfolio:
    def test_public_portfolio_requires_no_auth(self, client, auth_headers):
        create_project(client, auth_headers, title="Public Project")
        project = client.get("/api/v1/projects", headers=auth_headers).json()["items"][0]
        publish_project(client, auth_headers, project)
        client.put(
            "/api/v1/profile",
            headers=auth_headers,
            json={"display_name": "Dmitriy", "headline": "Python Developer"},
        )

        response = client.get("/api/v1/public/owner")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "owner"
        assert data["profile"]["display_name"] == "Dmitriy"
        assert len(data["projects"]) == 1
        assert data["projects"][0]["title"] == "Public Project"

    def test_draft_projects_not_in_public(self, client, auth_headers):
        draft = create_project(client, auth_headers, title="Secret Draft")
        published = create_project(client, auth_headers, title="Visible One")
        publish_project(client, auth_headers, published)

        response = client.get("/api/v1/public/owner")
        titles = [p["title"] for p in response.json()["projects"]]
        assert titles == ["Visible One"]
        assert "Secret Draft" not in titles

    def test_unpublished_then_published_reflects(self, client, auth_headers):
        project = create_project(client, auth_headers, title="Toggle")
        response = client.get("/api/v1/public/owner")
        assert response.json()["projects"] == []
        publish_project(client, auth_headers, project)
        response = client.get("/api/v1/public/owner")
        assert len(response.json()["projects"]) == 1

    def test_wrong_username_404(self, client):
        response = client.get("/api/v1/public/nosuchuser")
        assert response.status_code == 404

    def test_public_does_not_expose_email(self, client, auth_headers):
        create_project(client, auth_headers, title="Proj")
        project = client.get("/api/v1/projects", headers=auth_headers).json()["items"][0]
        publish_project(client, auth_headers, project)
        data = client.get("/api/v1/public/owner").json()
        assert "email" not in data["profile"]
        assert "password_hash" not in str(data)

    def test_skills_derived_from_published_projects(self, client, auth_headers):
        project = create_project(client, auth_headers, title="Stacked")
        techs = client.get("/api/v1/technologies").json()
        ids = [t["id"] for t in techs if t["name"] in ("Python", "FastAPI", "PostgreSQL")]
        client.put(
            f"/api/v1/projects/{project['id']}/technologies",
            headers=auth_headers,
            json={"technology_ids": ids},
        )
        publish_project(client, auth_headers, project)
        data = client.get("/api/v1/public/owner").json()
        assert set(data["skills"]) == {"Python", "FastAPI", "PostgreSQL"}


class TestPublicProject:
    def test_public_project_page(self, client, auth_headers):
        project = create_project(
            client,
            auth_headers,
            title="Case Study Project",
            problem="The problem",
            solution="The solution",
            result="The result",
            role="Backend Developer",
        )
        publish_project(client, auth_headers, project)
        response = client.get("/api/v1/public/owner/projects/case-study-project")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "owner"
        assert data["project"]["problem"] == "The problem"
        assert data["project"]["role"] == "Backend Developer"

    def test_draft_project_page_404(self, client, auth_headers):
        create_project(client, auth_headers, title="Hidden Draft")
        response = client.get("/api/v1/public/owner/projects/hidden-draft")
        assert response.status_code == 404

    def test_wrong_slug_404(self, client, auth_headers):
        project = create_project(client, auth_headers, title="Existing")
        publish_project(client, auth_headers, project)
        response = client.get("/api/v1/public/owner/projects/wrong-slug")
        assert response.status_code == 404

    def test_wrong_username_project_404(self, client, auth_headers):
        project = create_project(client, auth_headers, title="Mine")
        publish_project(client, auth_headers, project)
        response = client.get("/api/v1/public/impostor/projects/mine")
        assert response.status_code == 404

    def test_unpublish_hides_project_page(self, client, auth_headers):
        project = create_project(client, auth_headers, title="Temp Visible")
        publish_project(client, auth_headers, project)
        assert client.get("/api/v1/public/owner/projects/temp-visible").status_code == 200
        client.post(f"/api/v1/projects/{project['id']}/unpublish", headers=auth_headers)
        assert client.get("/api/v1/public/owner/projects/temp-visible").status_code == 404


class TestPublicPagination:
    def _publish_many(self, client, headers, count: int) -> None:
        for index in range(count):
            project = create_project(client, headers, title=f"Case {index}")
            publish_project(client, headers, project)

    def test_pagination_slices_projects(self, client, auth_headers):
        self._publish_many(client, auth_headers, 5)

        data = client.get("/api/v1/public/owner?page=1&limit=2").json()
        assert len(data["projects"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["limit"] == 2

    def test_pages_do_not_overlap(self, client, auth_headers):
        self._publish_many(client, auth_headers, 5)

        first = client.get("/api/v1/public/owner?page=1&limit=2").json()["projects"]
        second = client.get("/api/v1/public/owner?page=2&limit=2").json()["projects"]

        first_ids = {p["id"] for p in first}
        second_ids = {p["id"] for p in second}
        assert first_ids.isdisjoint(second_ids)

    def test_page_beyond_end_returns_empty_but_keeps_total(self, client, auth_headers):
        self._publish_many(client, auth_headers, 3)

        data = client.get("/api/v1/public/owner?page=9&limit=2").json()
        assert data["projects"] == []
        assert data["total"] == 3

    def test_skills_cover_all_pages_not_just_current(self, client, auth_headers):
        """The tech section describes the whole portfolio, so it must not shrink
        to whatever happens to be on page 2."""
        techs = client.get("/api/v1/technologies").json()
        python_id = next(t["id"] for t in techs if t["name"] == "Python")
        react_id = next(t["id"] for t in techs if t["name"] == "React")

        first = create_project(client, auth_headers, title="With Python")
        client.put(
            f"/api/v1/projects/{first['id']}/technologies",
            headers=auth_headers,
            json={"technology_ids": [python_id]},
        )
        publish_project(client, auth_headers, first)

        second = create_project(client, auth_headers, title="With React")
        client.put(
            f"/api/v1/projects/{second['id']}/technologies",
            headers=auth_headers,
            json={"technology_ids": [react_id]},
        )
        publish_project(client, auth_headers, second)

        page_two = client.get("/api/v1/public/owner?page=2&limit=1").json()
        assert len(page_two["projects"]) == 1
        assert set(page_two["skills"]) == {"Python", "React"}

    def test_without_params_returns_everything(self, client, auth_headers):
        self._publish_many(client, auth_headers, 4)

        data = client.get("/api/v1/public/owner").json()
        assert len(data["projects"]) == 4
        assert data["page"] is None

    def test_invalid_pagination_rejected(self, client, auth_headers):
        assert client.get("/api/v1/public/owner?page=0").status_code == 422
        assert client.get("/api/v1/public/owner?limit=0").status_code == 422
        assert client.get("/api/v1/public/owner?limit=999").status_code == 422


class TestSitemap:
    def test_sitemap_lists_published_pages_only(self, client, auth_headers):
        published = create_project(client, auth_headers, title="Public Case")
        publish_project(client, auth_headers, published)
        create_project(client, auth_headers, title="Hidden Draft")

        response = client.get("/api/v1/public/sitemap.xml")
        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        body = response.text
        assert "/owner" in body
        assert "/owner/projects/public-case" in body
        assert "hidden-draft" not in body

    def test_sitemap_uses_absolute_urls(self, client, auth_headers):
        body = client.get("/api/v1/public/sitemap.xml").text
        # Crawlers reject relative <loc> values.
        assert "<loc>http" in body
        assert body.startswith('<?xml version="1.0"')

    def test_sitemap_escapes_xml_entities(self, client, auth_headers):
        from app.utils.sitemap import render_sitemap

        xml = render_sitemap([("https://example.com/a?x=1&y=2", None)])
        assert "&amp;" in xml
        assert "?x=1&y=2" not in xml
