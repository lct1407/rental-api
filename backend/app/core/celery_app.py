"""
Celery application configuration
"""
from celery import Celery
from celery.schedules import crontab

from app.config import settings


# Create Celery app
celery_app = Celery(
    "rentapi",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.webhook_tasks",
        "app.tasks.email_tasks",
        "app.tasks.analytics_tasks",
        "app.tasks.subscription_tasks",
        "app.tasks.maintenance_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,

    # Result backend
    result_expires=3600,
    result_persistent=True,

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Task routing
    task_routes={
        "app.tasks.webhook_tasks.*": {"queue": "webhooks"},
        "app.tasks.email_tasks.*": {"queue": "emails"},
        "app.tasks.analytics_tasks.*": {"queue": "analytics"},
        "app.tasks.subscription_tasks.*": {"queue": "subscriptions"},
        "app.tasks.maintenance_tasks.*": {"queue": "maintenance"}
    },

    # Retry settings
    task_autoretry_for=(Exception,),
    task_retry_kwargs={"max_retries": 3, "countdown": 5},

    # Beat schedule (periodic tasks)
    beat_schedule={
        # Retry failed webhooks every 5 minutes
        "retry-failed-webhooks": {
            "task": "app.tasks.webhook_tasks.retry_failed_webhooks",
            "schedule": crontab(minute="*/5")
        },
        # Aggregate analytics every hour
        "aggregate-analytics": {
            "task": "app.tasks.analytics_tasks.aggregate_hourly_analytics",
            "schedule": crontab(minute=0)
        },
        # Check expiring subscriptions daily
        "check-expiring-subscriptions": {
            "task": "app.tasks.subscription_tasks.check_expiring_subscriptions",
            "schedule": crontab(hour=0, minute=0)
        },
        # Renew subscriptions daily
        "renew-subscriptions": {
            "task": "app.tasks.subscription_tasks.renew_subscriptions",
            "schedule": crontab(hour=1, minute=0)
        },
        # Clean up old logs weekly
        "cleanup-old-logs": {
            "task": "app.tasks.maintenance_tasks.cleanup_old_logs",
            "schedule": crontab(day_of_week=0, hour=2, minute=0)
        },
        # Generate daily reports
        "generate-daily-reports": {
            "task": "app.tasks.analytics_tasks.generate_daily_reports",
            "schedule": crontab(hour=3, minute=0)
        },
        # Check inactive API keys monthly
        "check-inactive-api-keys": {
            "task": "app.tasks.maintenance_tasks.check_inactive_api_keys",
            "schedule": crontab(day_of_month=1, hour=4, minute=0)
        }
    }
)


# Task base class with common functionality
class BaseTask(celery_app.Task):
    """Base task with error handling"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        print(f"Task {self.name} failed: {exc}")
        # You could send alerts, log to monitoring service, etc.

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry"""
        print(f"Task {self.name} retrying: {exc}")

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        print(f"Task {self.name} succeeded")


# Set as default task base class
celery_app.Task = BaseTask
