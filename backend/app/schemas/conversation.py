"""Conversation schemas."""
from marshmallow import Schema, fields

from .message import MessageSchema


class ConversationSchema(Schema):
    """Conversation list serialization schema."""
    id = fields.Int(dump_only=True)
    title = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    message_count = fields.Method('get_message_count')

    def get_message_count(self, obj):
        if hasattr(obj, 'messages'):
            return obj.messages.count() if hasattr(obj.messages, 'count') else len(obj.messages)
        return 0


class ConversationDetailSchema(ConversationSchema):
    """Conversation detail with messages."""
    messages = fields.Method('get_messages')

    def get_messages(self, obj):
        if hasattr(obj, 'messages'):
            messages = obj.messages.all() if hasattr(obj.messages, 'all') else obj.messages
            return MessageSchema(many=True).dump(messages)
        return []
