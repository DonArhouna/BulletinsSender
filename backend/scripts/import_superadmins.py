#!/usr/bin/env python3
"""Import superadmin rows from JSON file into table "user".

Assumes the database schema (table "user") already exists with compatible columns.
"""
import os, sys, json
try:
    import psycopg2
except Exception as e:
    print('psycopg2 missing', e, file=sys.stderr); sys.exit(2)

INP = os.path.join(os.path.dirname(__file__), '..', '.superadmins.json')
url = os.environ.get('DATABASE_URL')
if not url:
    print('DATABASE_URL not set', file=sys.stderr); sys.exit(2)

if not os.path.exists(INP):
    print(f'File not found: {INP}', file=sys.stderr); sys.exit(2)

with open(INP, 'r', encoding='utf-8') as f:
    data = json.load(f)

if not data:
    print('No admins to import'); sys.exit(0)

conn = psycopg2.connect(url)
try:
    conn.autocommit = True
    cur = conn.cursor()
    insert_sql = (
        'INSERT INTO "user" (email, username, hashed_password, full_name, company, is_active, is_superuser, first_login, tenant_id, subscription_plan_id, pricing_plan_id) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    )
    for a in data:
        cur.execute(insert_sql, (
            a.get('email'),
            a.get('username'),
            a.get('hashed_password'),
            a.get('full_name'),
            a.get('company'),
            a.get('is_active'),
            a.get('is_superuser'),
            a.get('first_login'),
            a.get('tenant_id'),
            a.get('subscription_plan_id'),
            a.get('pricing_plan_id'),
        ))
    cur.close()
    print(f'Imported {len(data)} superadmin(s)')
finally:
    conn.close()
