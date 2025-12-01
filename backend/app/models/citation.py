"""Citation model linking messages to source chunks."""
from datetime import datetime

from ..extensions import db


class Citation(db.Model):
    """Citation linking message to source document chunk."""
    __tablename__ = 'citations'

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)
    chunk_id = db.Column(db.Integer, db.ForeignKey('document_chunks.id'), nullable=False)
    relevance_score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Citation message={self.message_id} chunk={self.chunk_id} score={self.relevance_score}>'
