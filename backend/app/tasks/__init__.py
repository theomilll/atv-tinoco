"""Celery tasks."""
from .document_tasks import process_document_task, ingest_url_task

__all__ = ['process_document_task', 'ingest_url_task']
