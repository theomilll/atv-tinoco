"""Document API endpoints."""
import os
from datetime import datetime
from pathlib import Path

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from ..extensions import db, csrf
from ..models import Document
from ..schemas import DocumentSchema, DocumentDetailSchema
from ..services import URLIngestionService, process_document

bp = Blueprint('documents', __name__, url_prefix='/api/documents')


@bp.route('/', methods=['GET'])
@login_required
def list_documents():
    """List user's documents."""
    query = Document.query.filter_by(user_id=current_user.id)

    # Search filter
    search = request.args.get('search')
    if search:
        query = query.filter(Document.title.ilike(f'%{search}%'))

    # Status filter
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    documents = query.order_by(Document.created_at.desc()).all()
    return jsonify({'results': DocumentSchema(many=True).dump(documents)})


@bp.route('/<int:id>/', methods=['GET'])
@login_required
def get_document(id):
    """Get document detail."""
    document = Document.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return jsonify(DocumentDetailSchema().dump(document))


@bp.route('/', methods=['POST'])
@login_required
@csrf.exempt
def upload_document():
    """Upload a new document."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400

    title = request.form.get('title') or file.filename

    # Save file
    timestamp = datetime.utcnow().strftime('%Y/%m/%d')
    save_dir = Path(current_app.config['UPLOAD_FOLDER']) / 'documents' / timestamp
    save_dir.mkdir(parents=True, exist_ok=True)

    file_path = save_dir / file.filename
    counter = 1
    while file_path.exists():
        stem = Path(file.filename).stem
        suffix = Path(file.filename).suffix
        file_path = save_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    file.save(str(file_path))

    # Get file size
    file_size = os.path.getsize(file_path)

    # Create document
    document = Document(
        user_id=current_user.id,
        title=title,
        file=str(file_path.relative_to(current_app.config['UPLOAD_FOLDER'])),
        file_type=file.content_type or 'application/octet-stream',
        file_size=file_size,
        status='pending'
    )
    db.session.add(document)
    db.session.commit()

    # Process document (sync for now, can be async with Celery)
    try:
        process_document(document)
    except Exception as e:
        document.status = 'failed'
        db.session.commit()

    return jsonify(DocumentSchema().dump(document)), 201


@bp.route('/<int:id>/', methods=['DELETE'])
@login_required
@csrf.exempt
def delete_document(id):
    """Delete a document."""
    document = Document.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    # Delete file if exists
    if document.file:
        file_path = Path(current_app.config['UPLOAD_FOLDER']) / document.file
        if file_path.exists():
            os.remove(file_path)

    db.session.delete(document)
    db.session.commit()

    return '', 204


@bp.route('/from-url/', methods=['POST'])
@login_required
@csrf.exempt
def from_url():
    """Ingest document from URL."""
    data = request.get_json() or {}
    url = data.get('url')
    title = data.get('title')

    if not url:
        return jsonify({'error': 'URL required'}), 400

    try:
        service = URLIngestionService()
        document = service.create_document_from_url(
            url=url,
            user_id=current_user.id,
            title=title
        )
        return jsonify(DocumentSchema().dump(document)), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to ingest URL: {str(e)}'}), 500


@bp.route('/<int:id>/reprocess/', methods=['POST'])
@login_required
@csrf.exempt
def reprocess_document(id):
    """Reprocess a failed document."""
    document = Document.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if document.status not in ['failed', 'completed']:
        return jsonify({'error': 'Can only reprocess failed or completed documents'}), 400

    # Delete existing chunks (cascades to embeddings)
    for chunk in document.chunks.all():
        db.session.delete(chunk)
    db.session.commit()

    document.status = 'pending'
    db.session.commit()

    try:
        process_document(document)
        return jsonify(DocumentSchema().dump(document))
    except Exception as e:
        return jsonify({'error': f'Reprocessing failed: {str(e)}'}), 500
