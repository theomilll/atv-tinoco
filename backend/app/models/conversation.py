"""Conversation and Message models."""
from datetime import datetime

from ..extensions import db


class Conversation(db.Model):
    """Chat conversation/session."""
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = db.relationship(
        'Message',
        backref='conversation',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Message.created_at'
    )

    def __repr__(self):
        return f'<Conversation {self.id}: {self.title}>'


class Message(db.Model):
    """Individual message in a conversation."""
    __tablename__ = 'messages'

    ROLE_USER = 'user'
    ROLE_ASSISTANT = 'assistant'
    ROLE_SYSTEM = 'system'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # user, assistant, system
    content = db.Column(db.Text, nullable=False)
    attachments = db.Column(db.JSON, default=list)
    # Schema: [{"filename": str, "file_type": str, "file_path": str, "category": "image"|"document"}]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    citations = db.relationship(
        'Citation',
        backref='message',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Citation.relevance_score.desc()'
    )

    def __repr__(self):
        return f'<Message {self.role}: {self.content[:50]}>'
