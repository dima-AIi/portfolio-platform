"""Repair an account whose Cyrillic text was stored as literal "?" characters.

Creating the showcase account from a PowerShell prompt wrote the request body
in the console code page, so every non-ASCII character was replaced with U+003F
on the way in. The database now holds "?????? ?." instead of "Дмитрий К." — the
public page renders the question marks verbatim, and no amount of frontend work
can undo it.

This script re-sends the same copy the seeder uses, as UTF-8 from a file-backed
JSON body, then verifies the round trip by reading the public payload back and
checking the response is free of "?".

    python scripts/repair_text.py <base-url> <email> <password>
"""

import json
import sys
import urllib.error
import urllib.request

sys.path.insert(0, __file__.rsplit("\\", 1)[0])
from seed_showcase import ELORA_PROJECT, PROFILE  # noqa: E402

BROKEN = "?"


def call(method: str, path: str, base: str, token: str | None = None, body: dict | None = None):
    """Send one request.

    The body is encoded explicitly as UTF-8: relying on the platform default is
    what corrupted the text in the first place.
    """
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{base}{path}",
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return resp.status, resp.headers.get("set-cookie", ""), (
                json.loads(raw) if raw else None
            )
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, exc.headers.get("set-cookie", ""), (json.loads(raw) if raw else None)


def session_token(set_cookie: str) -> str:
    for part in set_cookie.split(";"):
        if part.strip().startswith("portfolio_session="):
            return part.split("=", 1)[1]
    return ""


def broken_fields(payload: dict) -> list[str]:
    """Names of text fields that still contain the placeholder character."""
    found = []

    def walk(prefix: str, node) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                walk(f"{prefix}.{key}" if prefix else key, value)
        elif isinstance(node, list):
            for value in node:
                walk(prefix, value)
        elif isinstance(node, str) and BROKEN in node:
            found.append(prefix)

    walk("", payload)
    return found


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 1
    base = sys.argv[1].rstrip("/") + "/api/v1"
    email, password = sys.argv[2], sys.argv[3]

    status, cookie, _ = call("POST", "/auth/login", base, body={"email": email, "password": password})
    token = session_token(cookie)
    if not token:
        print(f"FAIL login: {status} (check email and password)")
        return 1
    print(f"auth OK as {email}")

    status, _, data = call("GET", f"/auth/me", base, token=token)
    username = data["username"]
    print(f"account: @{username}")

    print("== profile ==")
    status, _, _ = call("PUT", "/profile", base, token, PROFILE)
    print(f"  {'OK' if status == 200 else 'FAIL'} -> {status}")

    print("== project ==")
    _, _, listing = call("GET", "/projects", base, token)
    items = listing.get("items", []) if isinstance(listing, dict) else []
    target = next((p for p in items if p["slug"] == "elora"), None)
    if target is None:
        print("  FAIL no elora project found")
        return 1
    status, _, _ = call("PUT", f"/projects/{target['id']}", base, token, ELORA_PROJECT)
    print(f"  {'OK' if status == 200 else 'FAIL'} updated {target['id']} -> {status}")

    print("== verify (public payload) ==")
    _, _, public = call("GET", f"/public/{username}", base)
    remaining = broken_fields(public)
    if remaining:
        print(f"  FAIL still corrupted: {', '.join(remaining)}")
        return 1
    name = public["profile"]["display_name"]
    print(f"  OK no '?' left; display_name={name!r}")
    print(f"\nRepaired https://{sys.argv[1]}/{username}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
