"""Document schemas."""
from marshmallow import Schema, fields


class DocumentChunkSchema(Schema):
    """DocumentChunk serialization schema."""
    id = fields.Int(dump_only=True)
    chunk_index = fields.Int()
    content = fields.Str()
    chunk_metadata = fields.Dict()
    created_at = fields.DateTime(dump_only=True)


class DocumentSchema(Schema):
    """Document list serialization schema."""
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    file = fields.Str()
    file_type = fields.Str()
    file_size = fields.Int()
    status = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    chunk_count = fields.Method('get_chunk_count')

    def get_chunk_count(self, obj):
        if hasattr(obj, 'chunks'):
            return obj.chunks.count() if hasattr(obj.chunks, 'count') else len(obj.chunks)
        return 0


class DocumentDetailSchema(DocumentSchema):
    """Document detail with chunks."""
    chunks = fields.Method('get_chunks')

    def get_chunks(self, obj):
        if hasattr(obj, 'chunks'):
            chunks = obj.chunks.all() if hasattr(obj.chunks, 'all') else obj.chunks
            return DocumentChunkSchema(many=True).dump(chunks)
        return []
