
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
