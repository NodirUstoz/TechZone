"""
Celery Worker Configuration and Entry Point

Run with:
    celery -A celery_worker.celery worker --loglevel=info
    celery -A celery_worker.celery beat --loglevel=info
"""
import os

from celery import Celery
from celery.schedules import crontab

from app import create_app


def make_celery(app_name: str = __name__) -> Celery:
    """
    Create and configure a Celery instance that integrates with the Flask app.
    """
    flask_app = create_app(os.getenv("FLASK_ENV", "development"))

    celery = Celery(
        app_name,
        broker=flask_app.config["CELERY_BROKER_URL"],
        backend=flask_app.config["CELERY_RESULT_BACKEND"],
    )

    celery.conf.update(
        # Serialization
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",

        # Timezone
        timezone="UTC",
        enable_utc=True,

        # Task settings
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,

        # Results
        result_expires=3600,  # 1 hour

        # Retry policy
        task_default_retry_delay=60,
        task_max_retries=3,

        # Beat schedule
        beat_schedule={
            "record-prices-every-6-hours": {
                "task": "app.tasks.price_tasks.record_prices",
                "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
            },
            "check-price-alerts-every-6-hours": {
                "task": "app.tasks.price_tasks.check_price_alerts",
                "schedule": crontab(minute=5, hour="*/6"),  # 5 minutes after price recording
            },
            "warranty-expiry-reminders-daily": {
                "task": "app.tasks.notification_tasks.check_warranty_expiry_reminders",
                "schedule": crontab(minute=0, hour=9),  # Daily at 9 AM UTC
            },
        },
    )

    # Auto-discover tasks in the app.tasks package
    celery.autodiscover_tasks(["app.tasks"])

    class ContextTask(celery.Task):
        """Ensure Flask app context is available inside Celery tasks."""
        abstract = True

        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery()
