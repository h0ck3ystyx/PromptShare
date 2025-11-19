"""Pytest configuration and fixtures."""

import os
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.database import Base, get_db
from src.main import app

# Test database URL (PostgreSQL for compatibility with PostgreSQL-specific types)
# Defaults to dockerized test database, can be overridden via TEST_DATABASE_URL env var
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://test_user:test_password@localhost:5433/test_promptshare",
)

# Ensure database URL uses psycopg driver for psycopg3
if TEST_DATABASE_URL.startswith("postgresql://") and "+psycopg" not in TEST_DATABASE_URL:
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)


def _check_database_connection() -> bool:
    """Check if test database is accessible."""
    try:
        test_engine = create_engine(
            TEST_DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 2},
        )
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _start_test_database() -> None:
    """Start test database using docker-compose if not already running."""
    if _check_database_connection():
        return  # Database is already available
    
    # Check if we're in CI environment - fail fast instead of skipping
    is_ci = os.getenv("CI") is not None or os.getenv("GITHUB_ACTIONS") is not None
    
    # Get project root (two levels up from backend/tests)
    project_root = Path(__file__).parent.parent.parent
    compose_file = project_root / "docker-compose.test.yml"
    
    if not compose_file.exists():
        if is_ci:
            pytest.fail(
                "docker-compose.test.yml not found and database not available. "
                "CI builds require a test database."
            )
        pytest.skip("docker-compose.test.yml not found and database not available")
    
    # Start docker-compose
    try:
        subprocess.run(
            ["docker-compose", "-f", str(compose_file), "up", "-d"],
            cwd=project_root,
            check=True,
            capture_output=True,
        )
        
        # Wait for database to be ready (max 30 seconds)
        max_wait = 30
        elapsed = 0
        while elapsed < max_wait:
            if _check_database_connection():
                return
            time.sleep(1)
            elapsed += 1
        
        if is_ci:
            pytest.fail(
                "Test database failed to start within 30 seconds. "
                "CI builds require a working test database."
            )
        pytest.skip("Test database failed to start within 30 seconds")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        if is_ci:
            pytest.fail(
                f"docker-compose not available or failed to start test database: {e}. "
                "CI builds require Docker and docker-compose."
            )
        pytest.skip("docker-compose not available or failed to start test database")


# Auto-start test database before any tests run
@pytest.fixture(scope="session", autouse=True)
def ensure_test_database():
    """Ensure test database is running before tests."""
    # Check if we're in CI environment - fail fast instead of skipping
    is_ci = os.getenv("CI") is not None or os.getenv("GITHUB_ACTIONS") is not None
    
    # Only auto-start if using default test database URL
    if TEST_DATABASE_URL == "postgresql+psycopg://test_user:test_password@localhost:5433/test_promptshare":
        _start_test_database()
    elif not _check_database_connection():
        if is_ci:
            pytest.fail(
                f"Test database not available at {TEST_DATABASE_URL}. "
                "CI builds require a working test database."
            )
        pytest.skip(f"Test database not available at {TEST_DATABASE_URL}")


# Verify database connection before creating engine
# This ensures we fail fast if DB is not available
if not _check_database_connection():
    is_ci = os.getenv("CI") is not None or os.getenv("GITHUB_ACTIONS") is not None
    if is_ci:
        pytest.fail(
            f"Test database not available at {TEST_DATABASE_URL}. "
            "CI builds require a working test database."
        )
    pytest.skip(f"Test database not available at {TEST_DATABASE_URL}")

engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    # Mock Celery task .delay() calls to execute synchronously in tests (no Redis required)
    # We need to patch the task objects that are imported in the services
    with patch("src.tasks.notifications.send_notification_task.delay") as mock_notif_delay, \
         patch("src.tasks.notifications.send_bulk_notifications_task.delay") as mock_bulk_delay:
        # Make tasks execute immediately by calling .run() when .delay() is called
        def sync_notif_task(*args, **kwargs):
            from src.tasks.notifications import send_notification_task
            # Create a mock task instance for DatabaseTask with db_session
            class MockTask:
                def __init__(self):
                    self._db = db_session
                @property
                def db(self):
                    return self._db
                def retry(self, *args, **kwargs):
                    raise Exception("Retry called")
            task_instance = MockTask()
            # Call the actual task function with task instance as first arg
            return send_notification_task(task_instance, *args, **kwargs)
        
        def sync_bulk_task(*args, **kwargs):
            from src.tasks.notifications import send_bulk_notifications_task
            # Patch SessionLocal to use test db_session for bulk task
            with patch("src.tasks.notifications.SessionLocal", return_value=db_session):
                return send_bulk_notifications_task.run(*args, **kwargs)
        
        mock_notif_delay.side_effect = sync_notif_task
        mock_bulk_delay.side_effect = sync_bulk_task
        
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.clear()

