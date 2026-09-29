"""Delete accounts by username, straight from the database.

The API has no "delete anybody" endpoint on purpose, so this is a
deliberate operator tool. It talks to PostgreSQL directly and is never
run by the app.

Dry-run is the default. Nothing is deleted until --confirm is passed,
and the account you name as KEEP is always spared:

    set DATABASE_URL=postgresql://...
    python scripts/remove_accounts.py demo demo-start
    python scripts/remove_accounts.py --confirm demo demo-start

Uploaded files are not touched: they live on the app server's disk, not
in the database, and are not reachable from here.
"""

import os
import sys

import psycopg2

sys.stdout.reconfigure(encoding="utf-8")

CONFIRM_FLAG = "--confirm"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
confirmed = CONFIRM_FLAG in sys.argv[1:]
keep = os.environ.get("KEEP_USERNAME", "").strip()

if not args:
    print(__doc__)
    sys.exit(1)

if keep and keep in args:
    print(f"refusing to delete the account named in KEEP_USERNAME ({keep})")
    sys.exit(1)

url = os.environ["DATABASE_URL"].replace("postgresql+psycopg2://", "postgresql://")
conn = psycopg2.connect(url, connect_timeout=15)
conn.set_session(autocommit=True)
cur = conn.cursor()

cur.execute(
    "select username, email, (select count(*) from projects p where p.user_id = u.id) "
    "from users u where username = any(%s) order by username",
    (args,),
)
found = cur.fetchall()
missing = set(args) - {row[0] for row in found}

print("найдены аккаунты:")
for username, email, projects in found:
    print(f"  @{username}  {email}  проектов: {projects}")
if missing:
    print("не найдены:", sorted(missing))
if not found:
    sys.exit(0)

# Deleting the user cascades to profile and projects. page_views has no ORM
# cascade and the FK is not enforced on every backend, so it is cleaned up
# explicitly rather than relying on the database.
if not confirmed:
    print("\nЭто сухой запуск. Ничего не удалено.")
    print("Повторите с --confirm, чтобы выполнить удаление.")
    conn.close()
    sys.exit(0)

for username, _email, _projects in found:
    cur.execute(
        "delete from page_views where user_id = (select id from users where username = %s)",
        (username,),
    )
    views = cur.rowcount
    cur.execute("delete from users where username = %s", (username,))
    print(f"  удалён @{username} (page_views: {views})")

cur.execute("delete from page_views where user_id not in (select id from users)")
print("осиротевших page_views удалено:", cur.rowcount)

cur.execute("select username from users order by created_at")
print("остались аккаунты:", [r[0] for r in cur.fetchall()])
conn.close()