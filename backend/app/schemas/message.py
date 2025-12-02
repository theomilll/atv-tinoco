"""Message schema."""
from marshmallow import Schema, fields


class MessageSchema(Schema):
    """Message serialization schema."""
    id = fields.Int(dump_only=True)
    role = fields.Str(required=True)
    content = fields.Str(required=True)
    attachments = fields.List(fields.Dict(), dump_default=[])
    created_at = fields.DateTime(dump_only=True)
