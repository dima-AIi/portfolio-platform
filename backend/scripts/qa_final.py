"""Final QA pass: exercises every page's API flows and edge cases.

Run with the backend on localhost:8000:
    python scripts/qa_final.py
"""

import json
import sys
import time
import urllib.error
import urllib.request
import uuid

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000") + "/api/v1"
RUN = str(int(time.time()))[-6:]
USER = f"qa{RUN}"
EMAIL = f"qa{RUN}@example.com"
PASSWORD = "qa-password-123"

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)

passed = 0
failed = []


def check(name: str, ok: bool, detail: str = "") -> None:
    global passed
    if ok:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed.append(name)
        print(f"  FAIL  {name}  {detail}")


def call(method: str, path: str, body=None, token=None, raw_body=None, content_type=None):
    data = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        method=method,
        headers={
            **({"Content-Type": content_type or "application/json"} if data else {}),
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = resp.read()
            try:
                return resp.status, json.loads(payload) if payload else None
            except json.JSONDecodeError:
                return resp.status, payload
    except urllib.error.HTTPError as e:
        payload = e.read()
        try:
            return e.code, json.loads(payload) if payload else None
        except json.JSONDecodeError:
            return e.code, payload


def unified_error(status_code, data) -> bool:
    return isinstance(data, dict) and "error" in data and "code" in data["error"]


def multipart(filename: str, content: bytes, mime: str):
    boundary = "----QABoundary"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f'filename="{filename}"\r\nContent-Type: {mime}\r\n\r\n'
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


print("== 1. REGISTER page ==")
s, d = call("POST", "/auth/register", {"email": EMAIL, "username": USER, "password": PASSWORD})
check("valid register -> 201 + token", s == 201 and d.get("access_token"), str(s))
token = d["access_token"]
s, d = call("POST", "/auth/register", {"email": EMAIL, "username": "x" + USER, "password": PASSWORD})
check("duplicate email -> 409 EMAIL_ALREADY_EXISTS", s == 409 and d["error"]["code"] == "EMAIL_ALREADY_EXISTS")
s, d = call("POST", "/auth/register", {"email": "other" + EMAIL, "username": USER, "password": PASSWORD})
check("duplicate username -> 409 USERNAME_ALREADY_EXISTS", s == 409 and d["error"]["code"] == "USERNAME_ALREADY_EXISTS")
s, d = call("POST", "/auth/register", {"email": "a@b.io", "username": "admin", "password": PASSWORD})
check("reserved username -> 422", s == 422 and unified_error(s, d))
s, d = call("POST", "/auth/register", {"email": "a@b.io", "username": "Bad Name", "password": PASSWORD})
check("invalid username -> 422", s == 422)
s, d = call("POST", "/auth/register", {"email": "a@b.io", "username": "okname", "password": "short"})
check("short password rejected (422 or 429 by rate limit)", s in (422, 429), str(s))
s, d = call("POST", "/auth/register", {"email": "not-an-email", "username": "okname2", "password": PASSWORD})
check("invalid email rejected (422 or 429 by rate limit)", s in (422, 429), str(s))

print("== 2. LOGIN page ==")
s, d = call("POST", "/auth/login", {"email": EMAIL.upper(), "password": PASSWORD})
check("login ok (case-insensitive email)", s == 200 and d.get("access_token"))
s, d = call("POST", "/auth/login", {"email": EMAIL, "password": "wrong-password"})
check("wrong password -> 401 INVALID_CREDENTIALS", s == 401 and d["error"]["code"] == "INVALID_CREDENTIALS")
s, d = call("POST", "/auth/login", {"email": "nobody@nowhere.io", "password": "whatever123"})
check("unknown email -> same 401 (no user enumeration)", s == 401 and d["error"]["code"] == "INVALID_CREDENTIALS")
s, d = call("GET", "/auth/me", token=token)
check("me with token -> 200", s == 200 and d["username"] == USER)
s, d = call("GET", "/auth/me")
check("me without token -> 401", s == 401)
s, d = call("GET", "/auth/me", token="garbage.token.value")
check("me with garbage token -> 401", s == 401)

print("== 3. DASHBOARD ==")
s, d = call("GET", "/profile", token=token)
check("profile loads (theme=classic, view_count=0)", s == 200 and d["theme"] == "classic" and d["view_count"] == 0)
s, d = call("GET", "/projects", token=token)
check("projects list empty", s == 200 and d["items"] == [] and d["total"] == 0)

print("== 4. PROFILE page ==")
s, d = call("PUT", "/profile", {
    "display_name": "QA Tester", "headline": "QA Engineer", "bio": "Testing everything.",
    "location": "Moscow", "website_url": "https://qa.example.com",
    "github_url": "https://github.com/qa", "telegram_url": "https://t.me/qa",
}, token=token)
check("profile update -> 200", s == 200 and d["display_name"] == "QA Tester")
s, d = call("PUT", "/profile", {"github_url": "javascript:alert(1)"}, token=token)
check("javascript: URL rejected -> 422 (XSS guard)", s == 422)
s, d = call("PUT", "/profile", {"bio": "x" * 2001}, token=token)
check("bio > 2000 rejected -> 422", s == 422)
body, ct = multipart("avatar.png", PNG, "image/png")
s, d = call("POST", "/profile/avatar", token=token, raw_body=body, content_type=ct)
check("avatar upload -> 200", s == 200 and d["avatar_url"].startswith("/uploads/"))
body, ct = multipart("evil.txt", b"not an image", "text/plain")
s, d = call("POST", "/profile/avatar", token=token, raw_body=body, content_type=ct)
check("avatar wrong type -> 400 INVALID_IMAGE", s == 400 and d["error"]["code"] == "INVALID_IMAGE")
body, ct = multipart("avatar.png", PNG, "image/png")
s, d = call("POST", "/profile/avatar", raw_body=body, content_type=ct)
check("avatar without auth -> 401", s == 401)

print("== 5. PROJECTS page (CRUD + slug) ==")
s, d = call("POST", "/projects", {"title": "Minimal Project"}, token=token)
check("create minimal -> 201 DRAFT", s == 201 and d["status"] == "DRAFT")
s, d = call("POST", "/projects", {"title": "Кириллица Проект"}, token=token)
check("cyrillic title -> transliterated slug", s == 201 and d["slug"] == "kirillitsa-proekt", str(d.get("slug")))
s, d = call("POST", "/projects", {"title": "Minimal Project"}, token=token)
check("duplicate title -> slug-2", s == 201 and d["slug"] == "minimal-project-2")
dup_slug_id = d["id"]
s, d = call("POST", "/projects", {"title": "!!! ??? ..."}, token=token)
check("special-chars-only title -> fallback slug", s == 201 and d["slug"] == "project", str(d.get("slug")))
weird_id = d["id"]
s, d = call("POST", "/projects", {"title": ""}, token=token)
check("empty title -> 422", s == 422)
s, d = call("POST", "/projects", {"title": "Long", "problem": "x" * 5001}, token=token)
check("problem > 5000 -> 422", s == 422)
s, d = call("GET", f"/projects/{dup_slug_id}", token=token)
check("get project by id", s == 200 and d["id"] == dup_slug_id)
s, d = call("GET", "/projects/not-a-uuid", token=token)
check("invalid uuid path -> 422 unified error", s == 422 and unified_error(s, d))
s, d = call("GET", f"/projects/{uuid.uuid4()}", token=token)
check("missing project -> 404 PROJECT_NOT_FOUND", s == 404 and d["error"]["code"] == "PROJECT_NOT_FOUND")
s, d = call("PUT", f"/projects/{weird_id}", {"result": "Only result field"}, token=token)
check("partial update keeps title", s == 200 and d["title"] == "!!! ??? ..." and d["result"] == "Only result field")
s, d = call("PUT", f"/projects/{weird_id}", {"github_url": "ftp://bad"}, token=token)
check("invalid github_url -> 422", s == 422)
s, d = call("DELETE", f"/projects/{dup_slug_id}", token=token)
check("delete -> 204", s == 204)
s, d = call("GET", f"/projects/{dup_slug_id}", token=token)
check("deleted project gone -> 404", s == 404)

print("== 6. PUBLISH + REORDER + PAGINATION ==")
s, p1 = call("POST", "/projects", {"title": "First Pub"}, token=token)
s, p2 = call("POST", "/projects", {"title": "Second Pub"}, token=token)
s, d = call("POST", f"/projects/{p1['id']}/publish", token=token)
check("publish -> PUBLISHED + published_at", s == 200 and d["status"] == "PUBLISHED" and d["published_at"])
s, d = call("POST", f"/projects/{p1['id']}/publish", token=token)
check("publish twice -> idempotent 200", s == 200)
s, d = call("POST", f"/projects/{p2['id']}/unpublish", token=token)
check("unpublish draft -> 200 DRAFT", s == 200 and d["status"] == "DRAFT")
s, d = call("PUT", "/projects/reorder", {"project_ids": [p2["id"], p1["id"]]}, token=token)
check("reorder -> 204", s == 204)
s, d = call("GET", "/projects", token=token)
check("reorder applied", [p["id"] for p in d["items"]][:2] == [p2["id"], p1["id"]])
s, d = call("PUT", "/projects/reorder", {"project_ids": [str(uuid.uuid4())]}, token=token)
check("reorder foreign id -> 400", s == 400)
s, d = call("PUT", "/projects/reorder", {"project_ids": []}, token=token)
check("reorder empty -> 422 (not swallowed by /{id})", s == 422)
s, d = call("GET", "/projects?page=1&limit=1", token=token)
check("pagination page=1 limit=1", s == 200 and len(d["items"]) == 1 and d["total"] >= 2)
s, d = call("GET", "/projects?page=0", token=token)
check("page=0 -> 422", s == 422)
s, d = call("GET", "/projects?limit=1000", token=token)
check("limit=1000 -> 422", s == 422)

print("== 7. TECHNOLOGIES ==")
s, techs = call("GET", "/technologies")
check("technologies list", s == 200 and len(techs) >= 20)
py = next(t["id"] for t in techs if t["name"] == "Python")
docker = next(t["id"] for t in techs if t["name"] == "Docker")
s, d = call("PUT", f"/projects/{p1['id']}/technologies", {"technology_ids": [py, docker]}, token=token)
check("set technologies -> 2", s == 200 and len(d["technologies"]) == 2)
s, d = call("PUT", f"/projects/{p1['id']}/technologies", {"technology_ids": [py]}, token=token)
check("replace technologies -> 1", s == 200 and len(d["technologies"]) == 1)
s, d = call("PUT", f"/projects/{p1['id']}/technologies", {"technology_ids": [str(uuid.uuid4())]}, token=token)
check("unknown technology id -> 400", s == 400)

print("== 8. IMAGES ==")
body, ct = multipart("cover.png", PNG, "image/png")
s, img = call("POST", f"/projects/{p1['id']}/images", token=token, raw_body=body, content_type=ct)
check("upload image -> 201", s == 201 and img["url"].startswith("/uploads/"))
check("random filename (no user filename)", "cover.png" not in img["url"])
s, d = call("PUT", f"/projects/{p1['id']}", {"cover_image_url": img["url"]}, token=token)
check("set cover -> 200", s == 200 and d["cover_image_url"] == img["url"])
s, d = call("DELETE", f"/projects/{p1['id']}/images/{img['id']}", token=token)
check("delete image -> 204", s == 204)
s, d = call("GET", f"/projects/{p1['id']}", token=token)
check("cover cleared after deleting cover image", d["cover_image_url"] is None)

print("== 9. PUBLIC pages ==")
s, d = call("GET", f"/public/{USER.upper()}")
check("public portfolio (uppercase username)", s == 200 and d["username"] == USER)
check("only published visible", [p["title"] for p in d["projects"]] == ["First Pub"])
check("no email/password in public payload", "email" not in json.dumps(d) and "password" not in json.dumps(d))
check("skills derived", d["skills"] == ["Python"])
s, d = call("GET", f"/public/{USER}/projects/first-pub")
check("public project page", s == 200 and d["project"]["title"] == "First Pub" and d["theme"] == "classic")
v1 = d["project"]["view_count"]
s, d = call("GET", f"/public/{USER}/projects/first-pub")
check("project view increments", d["project"]["view_count"] == v1 + 1)
s, d = call("GET", f"/public/{USER}/projects/second-pub")
check("draft project page -> 404", s == 404)
s, d = call("GET", "/public/nosuchuser999")
check("unknown portfolio -> 404 unified", s == 404 and unified_error(s, d))

print("== 10. SETTINGS page ==")
s, d = call("PUT", "/auth/password", {"current_password": "wrong", "new_password": "newpass-123"}, token=token)
check("password change wrong current -> 400", s == 400)
s, d = call("PUT", "/auth/password", {"current_password": PASSWORD, "new_password": "newpass-123"}, token=token)
check("password change -> 204", s == 204)
s, d = call("POST", "/auth/login", {"email": EMAIL, "password": "newpass-123"})
check("login with new password", s == 200)
token = d["access_token"]
s, d = call("PUT", "/auth/email", {"email": f"new{EMAIL}", "password": "wrong"}, token=token)
check("email change wrong password -> 400", s == 400)
s, d = call("PUT", "/auth/email", {"email": f"new{EMAIL}", "password": "newpass-123"}, token=token)
check("email change -> 200", s == 200 and d["email"] == f"new{EMAIL}")
s, d = call("PUT", "/auth/email", {"email": f"new{EMAIL}", "password": "newpass-123"}, token=token)
check("email change to own current email -> 200 (409-taken path covered by unit tests)", s == 200)

print("== 11. SECURITY edge cases ==")
s, d = call("POST", "/projects", {"title": "Robert'); DROP TABLE projects;--"}, token=token)
if s == 403:
    # Vercel WAF (production) blocks SQLi at the edge — also a valid outcome;
    # the "stored literally" path is proven by the localhost run.
    check("SQLi blocked (403 at edge by Vercel WAF)", True)
else:
    check("SQLi string stored literally", s == 201 and d["title"] == "Robert'); DROP TABLE projects;--")
s, d = call("GET", "/projects", token=token)
check("table intact after SQLi attempt", d["total"] >= 4)
s, d = call("POST", "/projects", {"title": "<script>alert(1)</script>"}, token=token)
check("script tag accepted as data (React escapes on render)", s == 201)
s, d = call("GET", "/uploads/../../app.db")
check("path traversal on uploads blocked", s in (404, 400), str(s))
s, d = call("GET", f"/public/{USER}")
check("still works after edge cases", s == 200)

print("== 12. ACCOUNT DELETION ==")
s, d = call("DELETE", "/auth/account", {"password": "wrong"}, token=token)
check("delete account wrong password -> 400", s == 400)
s, d = call("DELETE", "/auth/account", {"password": "newpass-123"}, token=token)
check("delete account -> 204", s == 204)
s, d = call("GET", f"/public/{USER}")
check("public page gone after deletion", s == 404)
s, d = call("POST", "/auth/login", {"email": f"new{EMAIL}", "password": "newpass-123"})
check("login impossible after deletion", s == 401)
# username-freed-after-deletion is covered by unit test
# test_username_freed_after_deletion (register rate limit applies here)

print("== 13. RATE LIMIT (last, it blocks logins) ==")
codes = []
for _ in range(12):
    s, _ = call("POST", "/auth/login", {"email": "nobody@nowhere.io", "password": "whatever123"})
    codes.append(s)
check("login rate limit triggers 429", 429 in codes, str(codes))

print()
print(f"RESULT: {passed} passed, {len(failed)} failed")
if failed:
    print("FAILED CHECKS:")
    for f in failed:
        print(" -", f)
    raise SystemExit(1)
