"""
User Marshmallow Schemas
"""
from marshmallow import Schema, fields, validate

from ..utils.validators import validate_password, validate_phone


class UserRegisterSchema(Schema):
    """Schema for user registration."""
    email = fields.Email(required=True)
    username = fields.String(
        required=True,
        validate=[
            validate.Length(min=3, max=80),
            validate.Regexp(
                r"^[a-zA-Z0-9_]+$",
                error="Username can only contain letters, numbers, and underscores.",
            ),
        ],
    )
    password = fields.String(required=True, validate=validate_password)
    first_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.String(required=True, validate=validate.Length(min=1, max=100))


class UserLoginSchema(Schema):
    """Schema for user login."""
    email = fields.Email(required=True)
    password = fields.String(required=True)


class UserUpdateSchema(Schema):
    """Schema for updating user profile."""
    username = fields.String(
        validate=[
            validate.Length(min=3, max=80),
            validate.Regexp(
                r"^[a-zA-Z0-9_]+$",
                error="Username can only contain letters, numbers, and underscores.",
            ),
        ],
    )
    first_name = fields.String(validate=validate.Length(min=1, max=100))
    last_name = fields.String(validate=validate.Length(min=1, max=100))
    phone = fields.String(validate=validate_phone)
    address_line1 = fields.String(validate=validate.Length(max=255))
    address_line2 = fields.String(validate=validate.Length(max=255), allow_none=True)
    city = fields.String(validate=validate.Length(max=100))
    state = fields.String(validate=validate.Length(max=100))
    zip_code = fields.String(validate=validate.Length(max=20))
    country = fields.String(validate=validate.Length(max=100))
    current_password = fields.String()
    new_password = fields.String(validate=validate_password)


class UserResponseSchema(Schema):
    """Schema for serializing user data in responses."""
    id = fields.Integer()
    email = fields.Email()
    username = fields.String()
    first_name = fields.String()
    last_name = fields.String()
    full_name = fields.String()
    phone = fields.String()
    avatar_url = fields.String()
    role = fields.String()
    is_active = fields.Boolean()
    email_verified = fields.Boolean()
    created_at = fields.DateTime()
    last_login = fields.DateTime()
