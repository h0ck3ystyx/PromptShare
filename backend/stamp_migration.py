#!/usr/bin/env python3
"""Stamp the database with the initial migration if enums exist but migration hasn't been recorded."""

import os
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:ChgMeS0m3t_m3123@localhost:5432/promptshare"
)

from sqlalchemy import create_engine, text
from src.config import settings

engine = create_engine(settings.database_url)

print(f"Checking database state: {settings.database_url}")

with engine.connect() as conn:
    # Check if alembic_version table exists
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'alembic_version'
        );
    """))
    has_version_table = result.scalar()
    
    # Check for enum types
    result = conn.execute(text("""
        SELECT typname FROM pg_type 
        WHERE typtype = 'e' 
        AND typname IN ('userrole', 'promptstatus', 'platformtag')
        ORDER BY typname;
    """))
    enums = [row[0] for row in result]
    print(f"Existing enum types: {enums}")
    
    # Check for some key tables
    result = conn.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('users', 'prompts', 'categories', 'collections')
        ORDER BY table_name;
    """))
    tables = [row[0] for row in result]
    print(f"Existing tables: {tables}")
    
    if not has_version_table and len(enums) == 3:
        print("\nEnums exist but migration not recorded. Creating alembic_version table...")
        conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('c4fc3a468ec0')"))
        conn.commit()
        print("✓ Stamped database with initial migration")
    elif has_version_table:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()
        print(f"\nCurrent migration version: {version}")
    else:
        print("\nDatabase state unclear. Run migrations normally.")

