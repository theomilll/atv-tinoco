"""Embedding model for vector storage."""
from datetime import datetime

from ..extensions import db


class Embedding(db.Model):
    """Vector embedding for document chunks."""
    __tablename__ = 'embeddings'

    id = db.Column(db.Integer, primary_key=True)
    chunk_id = db.Column(db.Integer, db.ForeignKey('document_chunks.id'), unique=True, nullable=False)
    vector = db.Column(db.JSON, nullable=False)  # Store as JSON array
    model_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Embedding for chunk {self.chunk_id}>'
