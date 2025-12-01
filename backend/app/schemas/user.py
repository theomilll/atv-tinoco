"""User schemas."""
from marshmallow import Schema, fields


class UserSchema(Schema):
    """User serialization schema."""
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    first_name = fields.Str()
    last_name = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
