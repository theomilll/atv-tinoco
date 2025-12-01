"""Celery tasks for document processing."""
from celery import shared_task

from ..extensions import db
from ..models import Document
from ..services import process_document, URLIngestionService


@shared_task
def process_document_task(document_id: int) -> dict:
    """Process a document asynchronously."""
    document = db.session.get(Document, document_id)
    if not document:
        return {'error': f'Document {document_id} not found'}

    try:
        process_document(document)
        return {'status': 'completed', 'document_id': document_id}
    except Exception as e:
        return {'status': 'failed', 'document_id': document_id, 'error': str(e)}


@shared_task
def ingest_url_task(url: str, user_id: int, title: str = None) -> dict:
    """Ingest a URL as a document asynchronously."""
    try:
        service = URLIngestionService()
        document = service.create_document_from_url(
            url=url,
            user_id=user_id,
            title=title
        )
        return {'status': 'completed', 'document_id': document.id}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}
