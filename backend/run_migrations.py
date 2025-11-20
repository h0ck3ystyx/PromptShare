#!/usr/bin/env python3
"""Run database migrations."""

import os
import sys

# Ensure we're using the correct database URL
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:ChgMeS0m3t_m3123@localhost:5432/promptshare"
)

from alembic import command
from alembic.config import Config

# Get the alembic.ini path
alembic_cfg = Config("alembic.ini")

print("Running database migrations...")
print(f"Database URL: {os.environ.get('DATABASE_URL', 'from config')}")

try:
    command.upgrade(alembic_cfg, "head")
    print("✓ Migrations completed successfully!")
except Exception as e:
    print(f"✗ Migration failed: {e}")
    sys.exit(1)

