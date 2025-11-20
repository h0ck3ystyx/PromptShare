#!/usr/bin/env python3
"""Test migration connection and state."""

import os
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:ChgMeS0m3t_m3123@localhost:5432/promptshare"
)

from sqlalchemy import create_engine, text
from src.config import settings

engine = create_engine(settings.database_url)

print(f"Connecting to: {settings.database_url}")

try:
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
        print(f"Alembic version table exists: {has_version_table}")
        
        if has_version_table:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            print(f"Current migration version: {version}")
        
        # Check for enum types
        result = conn.execute(text("""
            SELECT typname FROM pg_type 
            WHERE typtype = 'e' 
            AND typname IN ('userrole', 'promptstatus', 'platformtag', 'notificationtype')
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
        
except Exception as e:
    print(f"Error: {e}")

