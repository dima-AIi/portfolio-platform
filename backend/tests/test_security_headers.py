class TestSecurityHeaders:
    def test_hardening_headers_present(self, client):
        response = client.get("/api/v1/health")
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "camera=()" in response.headers["Permissions-Policy"]

    def test_hsts_when_https(self, client):
        response = client.get(
            "/api/v1/health", headers={"X-Forwarded-Proto": "https"}
        )
        assert "Strict-Transport-Security" in response.headers

    def test_no_hsts_on_plain_http(self, client):
        response = client.get("/api/v1/health")
        assert "Strict-Transport-Security" not in response.headers
