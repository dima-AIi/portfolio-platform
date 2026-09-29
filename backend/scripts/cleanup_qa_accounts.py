"""One-off cleanup: remove QA leftovers from the production database.

Deletes only accounts whose username starts with "probe" (created by automated
QA runs) plus their page_views. Real accounts are never touched.
"""

import os
import sys

import psycopg2

sys.stdout.reconfigure(encoding="utf-8")

url = os.environ["DATABASE_URL"].replace("postgresql+psycopg2://", "postgresql://")
conn = psycopg2.connect(url, connect_timeout=15)
conn.set_session(autocommit=True)
cur = conn.cursor()

cur.execute("select username from users where username like 'probe%'")
names = [r[0] for r in cur.fetchall()]
print("найдено тестовых аккаунтов:", names)

for name in names:
    cur.execute("delete from users where username = %s", (name,))
    print(f"  удалён {name}")

cur.execute("delete from page_views where user_id not in (select id from users)")
print("осиротевших page_views удалено:", cur.rowcount)

cur.execute("select username from users order by created_at")
print("остались аккаунты:", [r[0] for r in cur.fetchall()])
cur.execute("select count(*) from page_views")
print("page_views осталось:", cur.fetchone()[0])
conn.close()
