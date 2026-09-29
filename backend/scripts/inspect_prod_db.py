"""Read-only inspection of the production database behind Render.

Never writes: every statement here is a SELECT. Used to confirm which Neon
project the live backend talks to and what the ELORA case text really holds.

    $env:DATABASE_URL = "postgresql+psycopg2://..."
    python backend/scripts/inspect_prod_db.py
"""

import os
import sys

import psycopg2

QUERIES = {
    "server": "select current_database(), current_user, version()",
    "alembic": "select version_num from alembic_version",
    "tables": """
        select table_name from information_schema.tables
        where table_schema = 'public' order by table_name
    """,
    "counts": """
        select
          (select count(*) from users)         as users,
          (select count(*) from projects)      as projects,
          (select count(*) from technologies)  as technologies,
          (select count(*) from page_views)    as page_views
    """,
    "usernames": "select username, email from users order by created_at",
    "elora": """
        select p.slug, p.status, p.features
        from projects p join users u on u.id = p.user_id
        where u.username = 'dmitry'
    """,
}

# Printed instead of the real value so a screenshot never leaks the password.
SECRET_KEYS = ("password", "jwt_secret")


def main() -> int:
    url = os.environ.get("DATABASE_URL", "").replace("postgresql+psycopg2://", "postgresql://")
    if not url:
        print("Set DATABASE_URL first.")
        return 1
    # Hide credentials in anything we print back.
    redacted = url.split("@", 1)[-1]
    print(f"connecting to {redacted}\n")

    conn = psycopg2.connect(url, connect_timeout=15)
    conn.set_session(readonly=True, autocommit=True)
    try:
        for name, sql in QUERIES.items():
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description]
            print(f"== {name} ==")
            for row in rows:
                print("  " + " | ".join(
                    f"{c}={_safe(v)}" for c, v in zip(cols, row)
                ))
            print()
    finally:
        conn.close()
    return 0


def _safe(value: object) -> str:
    text = repr(value)
    for key in SECRET_KEYS:
        if key in text:
            return "<redacted>"
    return text


if __name__ == "__main__":
    sys.exit(main())
