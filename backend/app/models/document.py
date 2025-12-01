"""Document and DocumentChunk models."""
from datetime import datetime

from ..extensions import db


class Document(db.Model):
    """Uploaded document for knowledge base."""
    __tablename__ = 'documents'

    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    file = db.Column(db.String(500), default='')  # File path
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default=STATUS_PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chunks = db.relationship(
        'DocumentChunk',
        backref='document',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='DocumentChunk.chunk_index'
    )

    def __repr__(self):
        return f'<Document {self.title}>'


class DocumentChunk(db.Model):
    """Text chunk from a document for embeddings."""
    __tablename__ = 'document_chunks'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    chunk_metadata = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    embedding = db.relationship(
        'Embedding',
        backref='chunk',
        uselist=False,
        cascade='all, delete-orphan'
    )
    citations = db.relationship(
        'Citation',
        backref='chunk',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        db.UniqueConstraint('document_id', 'chunk_index', name='uq_document_chunk_index'),
    )

    def __repr__(self):
        return f'<DocumentChunk {self.document.title} - {self.chunk_index}>'
