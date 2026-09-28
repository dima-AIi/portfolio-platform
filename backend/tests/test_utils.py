from collections import deque

from app.utils.rate_limit import _MAX_TRACKED_KEYS, _buckets, _evict_idle
from app.utils.slug import is_valid_username, slugify, unique_slug


class TestRateLimitEviction:
    def _fill(self, count: int, now: float) -> None:
        _buckets.clear()
        for index in range(count):
            _buckets[f"10.0.0.{index % 250}:/api/v1/auth/login"] = deque([now])

    def test_idle_buckets_evicted_when_over_limit(self):
        now = 1000.0
        self._fill(_MAX_TRACKED_KEYS + 50, now - 7200)  # long-idle keys
        _buckets["10.0.1.1:/api/v1/auth/login"] = deque([now])

        _evict_idle(now)

        # Idle keys are dropped, the active one survives.
        assert "10.0.1.1:/api/v1/auth/login" in _buckets
        assert len(_buckets) < _MAX_TRACKED_KEYS + 50

    def test_active_buckets_survive_eviction(self):
        """Eviction must not hand an attacker a free reset of live limits."""
        now = 1000.0
        self._fill(20, now)  # all fresh

        _evict_idle(now)

        assert len(_buckets) == 20

    def test_store_never_exceeds_max_tracked_keys(self):
        now = 1000.0
        _buckets.clear()
        for index in range(_MAX_TRACKED_KEYS + 500):
            _buckets[f"10.0.0.1:{index}"] = deque([now])

        _evict_idle(now)

        assert len(_buckets) <= _MAX_TRACKED_KEYS

    def teardown_method(self):
        _buckets.clear()


class TestSlugify:
    def test_english(self):
        assert slugify("Telegram CRM") == "telegram-crm"

    def test_cyrillic(self):
        assert slugify("Телеграм CRM") == "telegram-crm"

    def test_special_chars(self):
        assert slugify("My App: v2.0!") == "my-app-v20"

    def test_empty(self):
        assert slugify("!!!") == ""

    def test_multiple_spaces(self):
        assert slugify("a   b\tc") == "a-b-c"


class TestUniqueSlug:
    def test_no_conflict(self):
        assert unique_slug("app", set()) == "app"

    def test_conflict(self):
        assert unique_slug("app", {"app"}) == "app-2"

    def test_multiple_conflicts(self):
        assert unique_slug("app", {"app", "app-2", "app-3"}) == "app-4"

    def test_empty_base(self):
        assert unique_slug("", set()) == "project"


class TestUsernameValidation:
    def test_valid(self):
        assert is_valid_username("dmitriy")
        assert is_valid_username("dev-dmitriy")
        assert is_valid_username("dev_1")

    def test_invalid(self):
        assert not is_valid_username("ab")
        assert not is_valid_username("Bad Name")
        assert not is_valid_username("user@example")

    def test_reserved(self):
        for name in ("login", "register", "dashboard", "api", "admin", "public"):
            assert not is_valid_username(name)
