# Celery Setup for Async Notifications

## Overview

Celery is used for asynchronous notification delivery to avoid blocking the FastAPI request/response cycle. Notifications are queued in Redis and processed by Celery workers.

## Prerequisites

1. Redis server running (used as Celery broker and result backend)
2. Celery and dependencies installed (`pip install -r requirements.txt`)

## Configuration

Add to your `.env` file:

```bash
# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email (Optional)
EMAIL_ENABLED=false
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password
EMAIL_FROM_ADDRESS=noreply@promptshare.com
EMAIL_FROM_NAME=PromptShare
```

## Running Celery Worker

Start the Celery worker in a separate terminal:

```bash
cd backend
source venv/bin/activate
celery -A celery_worker worker --loglevel=info
```

For development with auto-reload:

```bash
celery -A celery_worker worker --loglevel=info --reload
```

## How It Works

1. **Notification Trigger**: When a prompt is published/updated or a comment is added, the service queues a Celery task instead of creating notifications synchronously.

2. **Task Processing**: Celery worker picks up tasks from Redis queue and:
   - Creates notification records in the database
   - Optionally sends email notifications (if enabled)

3. **Deduplication**: Users following multiple categories for the same prompt receive only one notification.

## Tasks

- `notifications.send_notification`: Send notification to a single user
- `notifications.send_bulk_notifications`: Send notifications to multiple users (used for category followers)

## Monitoring

Check Celery task status:

```bash
# List active tasks
celery -A celery_worker inspect active

# List registered tasks
celery -A celery_worker inspect registered

# Check worker stats
celery -A celery_worker inspect stats
```

## Production Deployment

1. Run Celery worker as a systemd service or container
2. Use a process manager (supervisor, systemd) to ensure worker stays running
3. Monitor Redis queue size to detect backlog
4. Set up alerts for task failures
5. Configure email SMTP settings for production email service

## Troubleshooting

**Notifications not being created:**
- Ensure Celery worker is running
- Check Redis connection
- Verify task is being queued (check logs)

**Email not sending:**
- Verify `EMAIL_ENABLED=true` in `.env`
- Check SMTP credentials are correct
- Test SMTP connection independently

**Tasks failing:**
- Check Celery worker logs for errors
- Verify database connection in worker
- Check task retry configuration

