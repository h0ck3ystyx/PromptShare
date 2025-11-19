"""Celery application configuration."""

import os
from celery import Celery

from src.config import settings

# Use memory broker/backend for tests to avoid Redis dependency
is_testing = os.getenv("PYTEST_CURRENT_TEST") is not None
test_broker = "memory://" if is_testing else settings.celery_broker_url
test_backend = "cache+memory://" if is_testing else settings.celery_result_backend

# Create Celery app
celery_app = Celery(
    "promptshare",
    broker=test_broker,
    backend=test_backend,
    include=["src.tasks.notifications"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

