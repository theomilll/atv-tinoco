"""Celery worker entry point."""
from celery import Celery

from app import create_app
from app.config import Config


def make_celery(app_name=__name__):
    """Create Celery instance with Flask app context."""
    celery = Celery(
        app_name,
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND,
    )

    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
    )

    # Import tasks
    celery.autodiscover_tasks(['app.tasks'])

    class ContextTask(celery.Task):
        """Task with Flask app context."""
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    return celery


flask_app = create_app()
celery = make_celery()
