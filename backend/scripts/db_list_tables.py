#!/usr/bin/env python3
"""List tables in public schema (helper for debugging migrations)."""
import os
import sys
try:
    import psycopg2
except Exception as e:
    print("psycopg2 not installed in this environment:", e, file=sys.stderr)
    sys.exit(2)

url = os.environ.get('DATABASE_URL')
if not url:
    print('DATABASE_URL not set', file=sys.stderr)
    sys.exit(2)

conn = psycopg2.connect(url)
try:
    cur = conn.cursor()
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;")
    rows = cur.fetchall()
    if not rows:
        print('No tables found in public schema')
    else:
        print('Tables in public schema:')
        for r in rows:
            print(' -', r[0])
    cur.close()
finally:
    conn.close()
