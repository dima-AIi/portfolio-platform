import io

from tests.conftest import create_project

PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000a49444154789c6300010000050001"
    "0d0a2db40000000049454e44ae426082"
)


def png_file(filename="test.png", content=PNG_BYTES):
    return {"file": (filename, io.BytesIO(content), "image/png")}


class TestImageUpload:
    def test_upload_project_image(self, client, auth_headers):
        created = create_project(client, auth_headers)
        response = client.post(
            f"/api/v1/projects/{created['id']}/images", files=png_file(), headers=auth_headers
        )
        assert response.status_code == 201, response.text
        assert response.json()["url"].startswith("/uploads/")

    def test_upload_rejects_non_image(self, client, auth_headers):
        created = create_project(client, auth_headers)
        response = client.post(
            f"/api/v1/projects/{created['id']}/images",
            files={"file": ("doc.txt", io.BytesIO(b"hello"), "text/plain")},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_IMAGE"

    def test_upload_rejects_fake_png_content(self, client, auth_headers):
        """File renamed to .png but not actually a PNG -> magic-byte check must catch it."""
        created = create_project(client, auth_headers)
        response = client.post(
            f"/api/v1/projects/{created['id']}/images",
            files={"file": ("fake.png", io.BytesIO(b"<html>evil</html>"), "image/png")},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_IMAGE"

    def test_upload_by_other_user_denied(self, client, auth_headers, second_user_headers):
        created = create_project(client, auth_headers)
        response = client.post(
            f"/api/v1/projects/{created['id']}/images", files=png_file(), headers=second_user_headers
        )
        assert response.status_code == 404

    def test_delete_project_image(self, client, auth_headers):
        created = create_project(client, auth_headers)
        image = client.post(
            f"/api/v1/projects/{created['id']}/images", files=png_file(), headers=auth_headers
        ).json()
        response = client.delete(
            f"/api/v1/projects/{created['id']}/images/{image['id']}", headers=auth_headers
        )
        assert response.status_code == 204
        project = client.get(f"/api/v1/projects/{created['id']}", headers=auth_headers).json()
        assert project["images"] == []

    def test_delete_image_by_other_user_denied(self, client, auth_headers, second_user_headers):
        created = create_project(client, auth_headers)
        image = client.post(
            f"/api/v1/projects/{created['id']}/images", files=png_file(), headers=auth_headers
        ).json()
        response = client.delete(
            f"/api/v1/projects/{created['id']}/images/{image['id']}", headers=second_user_headers
        )
        assert response.status_code == 404

    def test_image_limit_enforced(self, client, auth_headers):
        from app.api.images import MAX_PROJECT_IMAGES

        created = create_project(client, auth_headers)
        for _ in range(MAX_PROJECT_IMAGES):
            response = client.post(
                f"/api/v1/projects/{created['id']}/images",
                files=png_file(),
                headers=auth_headers,
            )
            assert response.status_code == 201
        response = client.post(
            f"/api/v1/projects/{created['id']}/images", files=png_file(), headers=auth_headers
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "IMAGE_LIMIT_REACHED"


class TestAvatar:
    def test_upload_avatar(self, client, auth_headers):
        response = client.post("/api/v1/profile/avatar", files=png_file(), headers=auth_headers)
        assert response.status_code == 200, response.text
        url = response.json()["avatar_url"]
        assert url.startswith("/uploads/")
        profile = client.get("/api/v1/profile", headers=auth_headers).json()
        assert profile["avatar_url"] == url

    def test_avatar_rejects_non_image(self, client, auth_headers):
        response = client.post(
            "/api/v1/profile/avatar",
            files={"file": ("doc.txt", io.BytesIO(b"hello"), "text/plain")},
            headers=auth_headers,
        )
        assert response.status_code == 400
