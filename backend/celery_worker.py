"""Celery worker entry point.

Run with: celery -A celery_worker worker --loglevel=info
"""

from src.celery_app import celery_app

if __name__ == "__main__":
    celery_app.start()

