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

    def test_replacing_avatar_removes_previous_file(self, client, auth_headers):
        """The old avatar file is no longer referenced — it must not stay on disk."""
        import os

        from app.utils.images import uploads_dir

        first = client.post(
            "/api/v1/profile/avatar", files=png_file(), headers=auth_headers
        ).json()["avatar_url"]
        first_path = os.path.join(uploads_dir(), os.path.basename(first))
        assert os.path.isfile(first_path)

        second = client.post(
            "/api/v1/profile/avatar", files=png_file(), headers=auth_headers
        ).json()["avatar_url"]

        assert second != first
        assert not os.path.isfile(first_path), "previous avatar file was not removed"
        assert os.path.isfile(os.path.join(uploads_dir(), os.path.basename(second)))


class TestImageCleanup:
    def test_deleting_project_removes_image_files(self, client, auth_headers):
        import os

        from app.utils.images import uploads_dir

        created = create_project(client, auth_headers)
        image = client.post(
            f"/api/v1/projects/{created['id']}/images", files=png_file(), headers=auth_headers
        ).json()
        path = os.path.join(uploads_dir(), os.path.basename(image["url"]))
        assert os.path.isfile(path)

        assert (
            client.delete(f"/api/v1/projects/{created['id']}", headers=auth_headers).status_code
            == 204
        )
        assert not os.path.isfile(path), "image file outlived the deleted project"

    def test_deleting_account_removes_uploaded_files(self, client, auth_headers):
        import os

        from app.utils.images import uploads_dir

        created = create_project(client, auth_headers)
        image = client.post(
            f"/api/v1/projects/{created['id']}/images", files=png_file(), headers=auth_headers
        ).json()
        avatar = client.post(
            "/api/v1/profile/avatar", files=png_file(), headers=auth_headers
        ).json()["avatar_url"]

        paths = [
            os.path.join(uploads_dir(), os.path.basename(url)) for url in (image["url"], avatar)
        ]
        assert all(os.path.isfile(p) for p in paths)

        response = client.request(
            "DELETE", "/api/v1/auth/account", headers=auth_headers, json={"password": "strongpass123"}
        )
        assert response.status_code == 204, response.text
        assert not any(os.path.isfile(p) for p in paths), "files left after account deletion"

    def test_image_order_stays_dense_after_delete(self, client, auth_headers):
        """sort_order must be renumbered so a new upload cannot collide."""
        created = create_project(client, auth_headers)
        images = [
            client.post(
                f"/api/v1/projects/{created['id']}/images", files=png_file(), headers=auth_headers
            ).json()
            for _ in range(3)
        ]

        # Delete the first one — the gap would otherwise stay at sort_order 0.
        client.delete(
            f"/api/v1/projects/{created['id']}/images/{images[0]['id']}", headers=auth_headers
        )

        project = client.get(f"/api/v1/projects/{created['id']}", headers=auth_headers).json()
        orders = sorted(image["sort_order"] for image in project["images"])
        assert orders == [0, 1], f"expected a dense 0..n-1 sequence, got {orders}"

        new_image = client.post(
            f"/api/v1/projects/{created['id']}/images", files=png_file(), headers=auth_headers
        ).json()
        project = client.get(f"/api/v1/projects/{created['id']}", headers=auth_headers).json()
        orders = sorted(image["sort_order"] for image in project["images"])
        assert orders == [0, 1, 2], f"sort_order collision after re-upload: {orders}"
        assert new_image["sort_order"] == 2
