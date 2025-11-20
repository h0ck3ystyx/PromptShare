#!/usr/bin/env python3
"""Drop existing enums and re-run migrations from scratch."""

import os
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:ChgMeS0m3t_m3123@localhost:5432/promptshare"
)

from sqlalchemy import create_engine, text
from src.config import settings

engine = create_engine(settings.database_url)

print(f"Dropping existing enum types and alembic_version table...")
print(f"Database: {settings.database_url}")

with engine.begin() as conn:
    # Drop alembic_version table if it exists
    conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    print("✓ Dropped alembic_version table")
    
    # Drop enum types (CASCADE to handle dependencies)
    for enum_name in ['userrole', 'promptstatus', 'platformtag', 'notificationtype', 'analyticseventtype']:
        try:
            conn.execute(text(f"DROP TYPE IF EXISTS {enum_name} CASCADE"))
            print(f"✓ Dropped {enum_name} enum (if it existed)")
        except Exception as e:
            print(f"  Note: {enum_name} - {e}")

print("\n✓ Database cleaned. Now run: python run_migrations.py")

