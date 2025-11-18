#!/usr/bin/env python3
"""Create a minimal `user` table compatible with app.models.users for seeding.

This is a best-effort helper to recreate only the `user` table so `seed_admin.py`
can run and create the superadmin after a destructive reset when migrations
are not being applied.
"""
import os
import sys
try:
    import psycopg2
except Exception as e:
    print("psycopg2 not available:", e, file=sys.stderr)
    sys.exit(2)

url = os.environ.get('DATABASE_URL')
if not url:
    print('DATABASE_URL not set', file=sys.stderr)
    sys.exit(2)

create_sql = '''
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    username VARCHAR UNIQUE,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR,
    company VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    first_login BOOLEAN DEFAULT TRUE,
    subscription_plan_id INTEGER,
    pricing_plan_id INTEGER,
    tenant_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
'''

conn = psycopg2.connect(url)
try:
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(create_sql)
    cur.close()
    print("Created minimal 'user' table (if not existed).")
finally:
    conn.close()
