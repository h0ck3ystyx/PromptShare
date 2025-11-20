#!/usr/bin/env python3
"""Force reload migration and run with explicit import clearing."""

import os
import sys

# Clear all caches
if 'migrations' in sys.modules:
    del sys.modules['migrations']
if 'migrations.versions' in sys.modules:
    del sys.modules['migrations.versions']
if 'migrations.versions.c4fc3a468ec0_initial_migration' in sys.modules:
    del sys.modules['migrations.versions.c4fc3a468ec0_initial_migration']

# Clear __pycache__
import shutil
for root, dirs, files in os.walk('migrations'):
    if '__pycache__' in dirs:
        shutil.rmtree(os.path.join(root, '__pycache__'))

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:ChgMeS0m3t_m3123@localhost:5432/promptshare"
)

from alembic import command
from alembic.config import Config

alembic_cfg = Config("alembic.ini")

print("Running database migrations with forced reload...")
print(f"Database URL: {os.environ.get('DATABASE_URL', 'from config')}")

try:
    command.upgrade(alembic_cfg, "head")
    print("✓ Migrations completed successfully!")
except Exception as e:
    print(f"✗ Migration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

