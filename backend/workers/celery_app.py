"""Celery application configuration with result persistence intentionally disabled."""

from celery import Celery

from app.config import get_settings


def create_celery_app() -> Celery:
    """Create the worker shell; concrete tasks are added by their owning phases."""

    settings = get_settings()
    application = Celery(
        "text_to_sql_platform",
        broker=settings.celery_broker_url,
    )
    application.conf.update(
        task_ignore_result=True,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        task_track_started=True,
    )
    return application


celery_app = create_celery_app()
