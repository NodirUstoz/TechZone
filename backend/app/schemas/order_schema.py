"""
Order Marshmallow Schemas
"""
from marshmallow import Schema, fields, validate

from ..utils.validators import validate_quantity


class OrderItemSchema(Schema):
    """Schema for a single order item."""
    product_id = fields.Integer(required=True)
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))


class ShippingAddressSchema(Schema):
    """Schema for shipping address."""
    first_name = fields.String(validate=validate.Length(max=100))
    last_name = fields.String(validate=validate.Length(max=100))
    line1 = fields.String(required=True, validate=validate.Length(min=1, max=255))
    line2 = fields.String(validate=validate.Length(max=255), load_default=None)
    city = fields.String(required=True, validate=validate.Length(min=1, max=100))
    state = fields.String(required=True, validate=validate.Length(min=1, max=100))
    zip_code = fields.String(required=True, validate=validate.Length(min=1, max=20))
    country = fields.String(load_default="US", validate=validate.Length(max=100))


class OrderCreateSchema(Schema):
    """Schema for creating a new order."""
    items = fields.List(
        fields.Nested(OrderItemSchema),
        required=True,
        validate=validate.Length(min=1, error="Order must contain at least one item."),
    )
    shipping_address = fields.Nested(ShippingAddressSchema, load_default=None)
    customer_notes = fields.String(validate=validate.Length(max=1000), load_default=None)


class OrderUpdateSchema(Schema):
    """Schema for admin order updates."""
    status = fields.String(
        validate=validate.OneOf([
            "pending", "paid", "processing", "shipped", "delivered", "cancelled",
        ])
    )
    tracking_number = fields.String(validate=validate.Length(max=100))
    shipping_carrier = fields.String(validate=validate.Length(max=50))
    admin_notes = fields.String(validate=validate.Length(max=2000))


class OrderResponseSchema(Schema):
    """Schema for order response serialization."""
    id = fields.Integer()
    order_number = fields.String()
    status = fields.String()
    subtotal = fields.Float()
    tax_amount = fields.Float()
    shipping_amount = fields.Float()
    discount_amount = fields.Float()
    total = fields.Float()
    item_count = fields.Integer()
    tracking_number = fields.String()
    shipping_carrier = fields.String()
    created_at = fields.DateTime()
    shipped_at = fields.DateTime()
    delivered_at = fields.DateTime()
