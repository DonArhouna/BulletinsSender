#!/usr/bin/env python3
import os, sys
try:
    import psycopg2
except Exception as e:
    print('psycopg2 missing', e, file=sys.stderr); sys.exit(2)
url = os.environ.get('DATABASE_URL')
if not url:
    print('DATABASE_URL not set', file=sys.stderr); sys.exit(2)
conn = psycopg2.connect(url)
try:
    cur = conn.cursor()
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='user' ORDER BY ordinal_position;")
    rows = cur.fetchall()
    if not rows:
        print('No columns for table user (table may not exist)')
    else:
        print('Columns for table "user":')
        for c in rows:
            print(' -', c[0], c[1])
    cur.close()
finally:
    conn.close()
