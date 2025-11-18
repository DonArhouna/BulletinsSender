#!/usr/bin/env python3
"""Export superadmin rows from table "user" to JSON file."""
import os, sys, json
try:
    import psycopg2
except Exception as e:
    print('psycopg2 missing', e, file=sys.stderr); sys.exit(2)

OUT = os.path.join(os.path.dirname(__file__), '..', '.superadmins.json')
url = os.environ.get('DATABASE_URL')
if not url:
    print('DATABASE_URL not set', file=sys.stderr); sys.exit(2)

conn = psycopg2.connect(url)
try:
    cur = conn.cursor()
    cur.execute(
        'SELECT email, username, hashed_password, full_name, company, is_active, is_superuser, first_login, tenant_id, subscription_plan_id, pricing_plan_id FROM "user" WHERE is_superuser = TRUE;'
    )
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    data = [dict(zip(cols, r)) for r in rows]
    cur.close()
finally:
    conn.close()

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'Exported {len(data)} superadmin(s) to {OUT}')
