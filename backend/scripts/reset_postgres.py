#!/usr/bin/env python3
"""
Simple, safe-ish Postgres reset helper for local/dev use.

What it does:
 - Reads DATABASE_URL from environment (e.g. postgres://user:pass@host:port/dbname)
 - Asks for interactive confirmation (type the database name to confirm)
 - Connects and runs: DROP SCHEMA public CASCADE; CREATE SCHEMA public;
 - Prints next steps (run alembic/prisma migrations or seed data)

Important: This is destructive. Use only on dev/test databases. Back up production first.
"""
import os
import sys
import urllib.parse
import argparse
import subprocess
import psycopg2
from psycopg2 import sql


def get_database_name(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        # path may start with '/'
        return parsed.path.lstrip('/')
    except Exception:
        return ''


def confirm(dbname: str) -> bool:
    prompt = (
        f"WARNING: This will DROP and RECREATE schema 'public' in database '{dbname}'.\n"
        "Type the database name to confirm: "
    )
    answer = input(prompt).strip()
    return answer == dbname


def reset_schema(database_url: str) -> None:
    conn = None
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("DROP SCHEMA public CASCADE;")
        cur.execute("CREATE SCHEMA public;")
        cur.close()
        print("Schema 'public' dropped and recreated successfully.")
    finally:
        if conn:
            conn.close()


def fetch_superadmins(database_url: str):
    """Return list of dicts for rows where is_superuser = true in table "user".
    If no such rows, returns empty list.
    """
    conn = psycopg2.connect(database_url)
    try:
        cur = conn.cursor()
        cur.execute(
            'SELECT email, username, hashed_password, full_name, company, is_active, is_superuser, first_login, tenant_id FROM "user" WHERE is_superuser = TRUE;'
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        results = [dict(zip(cols, row)) for row in rows]
        cur.close()
        return results
    finally:
        conn.close()


def reinsert_superadmins(database_url: str, admins: list):
    if not admins:
        print("No superadmin rows to reinsert.")
        return
    conn = psycopg2.connect(database_url)
    try:
        conn.autocommit = True
        cur = conn.cursor()
        insert_sql = (
            'INSERT INTO "user" (email, username, hashed_password, full_name, company, is_active, is_superuser, first_login, tenant_id) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
        )
        for a in admins:
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
            ))
        cur.close()
        print(f"Reinserted {len(admins)} superadmin(s) into 'user' table.")
    finally:
        conn.close()


def run_alembic_upgrade(backend_dir: str):
    """Run `alembic upgrade head` in the backend directory. Raises CalledProcessError on failure."""
    print("Running migrations: alembic upgrade head")
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True, cwd=backend_dir)


def main():
    parser = argparse.ArgumentParser(description="Reset Postgres public schema. Optionally keep superadmin(s) and re-run migrations.")
    parser.add_argument('--keep-superadmin', action='store_true', help='Preserve rows where is_superuser = TRUE and reinsert them after reset + migrations')
    parser.add_argument('--no-migrate', action='store_true', help='Do not run alembic migrations after schema reset')
    args = parser.parse_args()

    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL environment variable is not set.\nExample: set it in PowerShell:\n  $env:DATABASE_URL='postgres://user:pass@localhost:5432/dbname'", file=sys.stderr)
        sys.exit(2)

    dbname = get_database_name(database_url)
    if not dbname:
        print("Could not parse database name from DATABASE_URL.", file=sys.stderr)
        sys.exit(2)

    if not confirm(dbname):
        print("Confirmation mismatch — aborting.")
        sys.exit(1)

    admins = []
    if args.keep_superadmin:
        try:
            admins = fetch_superadmins(database_url)
            print(f"Found {len(admins)} superadmin(s) to preserve.")
        except Exception as exc:
            print(f"Error fetching superadmin(s): {exc}", file=sys.stderr)
            sys.exit(4)

    try:
        reset_schema(database_url)
    except Exception as exc:
        print(f"Error resetting schema: {exc}", file=sys.stderr)
        sys.exit(3)

    # Optionally run migrations
    if not args.no_migrate:
        try:
            backend_dir = os.path.join(os.path.dirname(__file__), '..')
            backend_dir = os.path.abspath(backend_dir)
            run_alembic_upgrade(backend_dir)
        except subprocess.CalledProcessError as exc:
            print(f"Migration command failed: {exc}", file=sys.stderr)
            sys.exit(5)

    # Reinsert preserved admins if any
    if args.keep_superadmin and admins:
        try:
            reinsert_superadmins(database_url, admins)
        except Exception as exc:
            print(f"Error reinserting superadmin(s): {exc}", file=sys.stderr)
            sys.exit(6)

    print("\nNext steps:")
    print(" - Verify the application starts and admin login works.")
    print(" - Run any additional seed scripts you need, e.g. python backend/seed_admin.py")


if __name__ == '__main__':
    main()
