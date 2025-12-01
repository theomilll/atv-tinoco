"""Message and Citation schemas."""
from marshmallow import Schema, fields


class CitationSchema(Schema):
    """Citation serialization schema."""
    document_title = fields.Method('get_document_title')
    chunk_content = fields.Method('get_chunk_content')
    chunk_index = fields.Method('get_chunk_index')
    relevance_score = fields.Float()

    def get_document_title(self, obj):
        return obj.chunk.document.title if obj.chunk else None

    def get_chunk_content(self, obj):
        return obj.chunk.content if obj.chunk else None

    def get_chunk_index(self, obj):
        return obj.chunk.chunk_index if obj.chunk else None


class MessageSchema(Schema):
    """Message serialization schema."""
    id = fields.Int(dump_only=True)
    role = fields.Str(required=True)
    content = fields.Str(required=True)
    attachments = fields.List(fields.Dict(), dump_default=[])
    created_at = fields.DateTime(dump_only=True)
    citations = fields.Method('get_citations')

    def get_citations(self, obj):
        if hasattr(obj, 'citations') and obj.role == 'assistant':
            citations = obj.citations.all() if hasattr(obj.citations, 'all') else obj.citations
            return CitationSchema(many=True).dump(citations)
        return []
