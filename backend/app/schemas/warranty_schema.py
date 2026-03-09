"""
Warranty Marshmallow Schemas
"""
from marshmallow import Schema, fields, validate, validates, ValidationError
from datetime import date


class WarrantyRegisterSchema(Schema):
    """Schema for registering a product warranty."""
    product_id = fields.Integer(required=True)
    order_item_id = fields.Integer(load_default=None, allow_none=True)
    serial_number = fields.String(
        required=True,
        validate=[
            validate.Length(min=3, max=100),
            validate.Regexp(
                r"^[A-Za-z0-9\-_]+$",
                error="Serial number can only contain letters, numbers, dashes, and underscores.",
            ),
        ],
    )
    purchase_date = fields.Date(required=True)

    @validates("purchase_date")
    def validate_purchase_date(self, value):
        if value > date.today():
            raise ValidationError("Purchase date cannot be in the future.")
        # Reject dates older than 5 years
        from dateutil.relativedelta import relativedelta
        oldest_allowed = date.today() - relativedelta(years=5)
        if value < oldest_allowed:
            raise ValidationError("Purchase date is too far in the past (maximum 5 years).")


class WarrantyClaimSchema(Schema):
    """Schema for submitting a warranty claim."""
    description = fields.String(
        required=True,
        validate=validate.Length(min=20, max=5000),
    )


class WarrantyClaimResolveSchema(Schema):
    """Schema for resolving a warranty claim (admin only)."""
    approved = fields.Boolean(required=True)
    resolution_notes = fields.String(
        required=True,
        validate=validate.Length(min=10, max=2000),
    )


class WarrantyFilterSchema(Schema):
    """Schema for warranty listing query parameters."""
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))
    status = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.OneOf(["active", "expired", "claimed", "void"]),
    )
    claim_status = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.OneOf(["none", "submitted", "in_review", "approved", "rejected", "resolved"]),
    )


class WarrantyResponseSchema(Schema):
    """Schema for serializing warranty data in responses."""
    id = fields.Integer()
    user_id = fields.Integer()
    product_id = fields.Integer()
    product_name = fields.String()
    serial_number = fields.String()
    purchase_date = fields.Date()
    warranty_start = fields.Date()
    warranty_end = fields.Date()
    status = fields.String()
    days_remaining = fields.Integer()
    claim_status = fields.String()
    created_at = fields.DateTime()
