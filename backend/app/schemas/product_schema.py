"""
Product Marshmallow Schemas
"""
from marshmallow import Schema, fields, validate

from ..utils.validators import validate_sku, validate_price


class SpecificationSchema(Schema):
    """Schema for a product specification entry."""
    group = fields.String(validate=validate.Length(max=100), load_default=None)
    key = fields.String(required=True, validate=validate.Length(min=1, max=100))
    value = fields.String(required=True, validate=validate.Length(min=1, max=500))
    sort_order = fields.Integer(load_default=0)


class ProductImageSchema(Schema):
    """Schema for a product image."""
    url = fields.URL(required=True)
    alt_text = fields.String(validate=validate.Length(max=255), load_default=None)
    is_primary = fields.Boolean(load_default=False)
    sort_order = fields.Integer(load_default=0)


class ProductCreateSchema(Schema):
    """Schema for creating a new product."""
    name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    sku = fields.String(required=True, validate=validate_sku)
    description = fields.String(load_default=None)
    short_description = fields.String(validate=validate.Length(max=500), load_default=None)

    price = fields.Float(required=True, validate=validate.Range(min=0.01))
    compare_at_price = fields.Float(validate=validate.Range(min=0), load_default=None)
    cost_price = fields.Float(validate=validate.Range(min=0), load_default=None)

    stock_quantity = fields.Integer(load_default=0, validate=validate.Range(min=0))
    low_stock_threshold = fields.Integer(load_default=5, validate=validate.Range(min=0))
    is_featured = fields.Boolean(load_default=False)

    weight_kg = fields.Float(load_default=None)
    length_cm = fields.Float(load_default=None)
    width_cm = fields.Float(load_default=None)
    height_cm = fields.Float(load_default=None)

    warranty_months = fields.Integer(load_default=12, validate=validate.Range(min=0))

    meta_title = fields.String(validate=validate.Length(max=255), load_default=None)
    meta_description = fields.String(validate=validate.Length(max=500), load_default=None)

    category_id = fields.Integer(required=True)
    brand_id = fields.Integer(required=True)

    specifications = fields.List(fields.Nested(SpecificationSchema), load_default=[])
    images = fields.List(fields.Nested(ProductImageSchema), load_default=[])


class ProductUpdateSchema(Schema):
    """Schema for updating a product (all fields optional)."""
    name = fields.String(validate=validate.Length(min=2, max=255))
    description = fields.String()
    short_description = fields.String(validate=validate.Length(max=500))

    price = fields.Float(validate=validate.Range(min=0.01))
    compare_at_price = fields.Float(validate=validate.Range(min=0), allow_none=True)
    cost_price = fields.Float(validate=validate.Range(min=0), allow_none=True)

    stock_quantity = fields.Integer(validate=validate.Range(min=0))
    low_stock_threshold = fields.Integer(validate=validate.Range(min=0))
    is_featured = fields.Boolean()
    is_active = fields.Boolean()

    weight_kg = fields.Float(allow_none=True)
    length_cm = fields.Float(allow_none=True)
    width_cm = fields.Float(allow_none=True)
    height_cm = fields.Float(allow_none=True)

    warranty_months = fields.Integer(validate=validate.Range(min=0))

    meta_title = fields.String(validate=validate.Length(max=255), allow_none=True)
    meta_description = fields.String(validate=validate.Length(max=500), allow_none=True)

    category_id = fields.Integer()
    brand_id = fields.Integer()

    specifications = fields.List(fields.Nested(SpecificationSchema))
    images = fields.List(fields.Nested(ProductImageSchema))


class ProductFilterSchema(Schema):
    """Schema for product list query parameters."""
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))
    category_id = fields.Integer(load_default=None)
    brand_id = fields.Integer(load_default=None)
    min_price = fields.Float(load_default=None)
    max_price = fields.Float(load_default=None)
    in_stock = fields.Boolean(load_default=None)
    is_featured = fields.Boolean(load_default=None)
    sort = fields.String(
        load_default="created_at",
        validate=validate.OneOf(["price", "name", "created_at", "rating"]),
    )
    order = fields.String(
        load_default="desc",
        validate=validate.OneOf(["asc", "desc"]),
    )
