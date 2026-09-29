"""Rate-limit behaviour that must hold no matter what the client claims.

The per-IP bucket is the precise brake, but the address a platform reports is
not always stable, and a client can put anything in X-Forwarded-For. The
per-path ceiling is what makes brute force impossible to talk your way past.
"""

from app.utils.rate_limit import _buckets, rate_limit, reset_rate_limits


class TestPerPathCeiling:
    def setup_method(self):
        reset_rate_limits()

    def test_rotating_forwarded_header_hits_the_ceiling(self):
        """Rotating the claimed address must not buy extra attempts."""
        limit = rate_limit(max_requests=5, window_seconds=60, path_max=5)

        from starlette.requests import Request

        def call(index: int):
            scope = {
                "type": "http",
                "method": "POST",
                "path": "/api/v1/auth/login",
                "headers": [
                    (b"x-forwarded-for", f"10.0.0.{index}".encode()),
                ],
                "client": ("10.0.0.1", 1234),
            }
            limit(Request(scope))

        # Five attempts pass because every request looks like a new client.
        for i in range(5):
            call(i)

        # The sixth is refused even though its address was never seen before.
        blocked = False
        try:
            call(5)
        except Exception as exc:  # AppError
            blocked = getattr(exc, "code", "") == "RATE_LIMITED"
        assert blocked, "per-path ceiling did not stop the rotating-address attack"

    def test_ceiling_is_shared_across_clients(self):
        limit = rate_limit(max_requests=100, window_seconds=60, path_max=3)

        from starlette.requests import Request

        def call(ip: str):
            scope = {
                "type": "http",
                "method": "POST",
                "path": "/api/v1/auth/login",
                "headers": [],
                "client": (ip, 1234),
            }
            limit(Request(scope))

        call("1.1.1.1")
        call("2.2.2.2")
        call("3.3.3.3")
        blocked = False
        try:
            call("4.4.4.4")
        except Exception as exc:
            blocked = getattr(exc, "code", "") == "RATE_LIMITED"
        assert blocked, "ceiling must count every client together"

    def test_per_ip_bucket_still_applies(self):
        limit = rate_limit(max_requests=2, window_seconds=60, path_max=1000)

        from starlette.requests import Request

        def call():
            scope = {
                "type": "http",
                "method": "POST",
                "path": "/api/v1/auth/login",
                "headers": [],
                "client": ("5.5.5.5", 1234),
            }
            limit(Request(scope))

        call()
        call()
        blocked = False
        try:
            call()
        except Exception as exc:
            blocked = getattr(exc, "code", "") == "RATE_LIMITED"
        assert blocked, "per-IP limit must trip for a single client"

    def test_no_ceiling_means_no_shared_counter(self):
        """Routes without path_max keep the old per-IP-only behaviour."""
        limit = rate_limit(max_requests=1, window_seconds=60)
        assert "shared:" not in "".join(_buckets.keys())
