#!/usr/bin/env python3
"""Fix migration by dropping existing enums and re-running, or stamping if needed."""

import os
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:ChgMeS0m3t_m3123@localhost:5432/promptshare"
)

from sqlalchemy import create_engine, text
from src.config import settings

engine = create_engine(settings.database_url)

print(f"Checking and fixing database: {settings.database_url}")

with engine.begin() as conn:  # Use begin() for transaction
    # Check if alembic_version table exists
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'alembic_version'
        );
    """))
    has_version_table = result.scalar()
    
    # Check for enum types in public schema
    result = conn.execute(text("""
        SELECT typname FROM pg_type t
        JOIN pg_namespace n ON t.typnamespace = n.oid
        WHERE n.nspname = 'public' 
        AND typtype = 'e' 
        AND typname IN ('userrole', 'promptstatus', 'platformtag')
        ORDER BY typname;
    """))
    enums = [row[0] for row in result]
    print(f"Existing enum types in public schema: {enums}")
    
    # Check for tables
    result = conn.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('users', 'prompts', 'categories', 'collections', 'alembic_version')
        ORDER BY table_name;
    """))
    tables = [row[0] for row in result]
    print(f"Existing tables: {tables}")
    
    if 'userrole' in enums or 'promptstatus' in enums or 'platformtag' in enums:
        if not has_version_table:
            print("\nEnums exist but migration not recorded. Creating alembic_version and stamping...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL, 
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                )
            """))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('c4fc3a468ec0') ON CONFLICT DO NOTHING"))
            print("✓ Stamped database with initial migration")
        else:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar() if result.rowcount > 0 else None
            print(f"\nCurrent migration version: {version}")
            if version is None:
                print("Stamping with initial migration...")
                conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('c4fc3a468ec0') ON CONFLICT DO NOTHING"))
    else:
        print("\nNo enum types found. Database is clean - migrations should run normally.")

