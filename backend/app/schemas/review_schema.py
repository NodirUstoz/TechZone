"""
Review Marshmallow Schemas
"""
from marshmallow import Schema, fields, validate, validates, ValidationError

from ..utils.validators import validate_rating


class ReviewCreateSchema(Schema):
    """Schema for creating a user product review."""
    rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    title = fields.String(validate=validate.Length(max=200), load_default=None)
    body = fields.String(validate=validate.Length(max=5000), load_default=None)
    pros = fields.List(fields.String(validate=validate.Length(max=200)), load_default=[])
    cons = fields.List(fields.String(validate=validate.Length(max=200)), load_default=[])

    @validates("pros")
    def validate_pros_count(self, value):
        if len(value) > 10:
            raise ValidationError("Cannot specify more than 10 pros.")

    @validates("cons")
    def validate_cons_count(self, value):
        if len(value) > 10:
            raise ValidationError("Cannot specify more than 10 cons.")


class ReviewUpdateSchema(Schema):
    """Schema for updating an existing review."""
    rating = fields.Integer(validate=validate.Range(min=1, max=5))
    title = fields.String(validate=validate.Length(max=200), allow_none=True)
    body = fields.String(validate=validate.Length(max=5000), allow_none=True)
    pros = fields.List(fields.String(validate=validate.Length(max=200)))
    cons = fields.List(fields.String(validate=validate.Length(max=200)))


class TechReviewCreateSchema(Schema):
    """Schema for creating a professional tech review (admin only)."""
    title = fields.String(required=True, validate=validate.Length(min=5, max=300))
    summary = fields.String(required=True, validate=validate.Length(min=20, max=2000))
    body = fields.String(required=True, validate=validate.Length(min=100))
    verdict = fields.String(required=True, validate=validate.Length(min=20, max=2000))

    score_performance = fields.Float(required=True, validate=validate.Range(min=1.0, max=10.0))
    score_value = fields.Float(required=True, validate=validate.Range(min=1.0, max=10.0))
    score_design = fields.Float(required=True, validate=validate.Range(min=1.0, max=10.0))
    score_features = fields.Float(required=True, validate=validate.Range(min=1.0, max=10.0))
    score_battery = fields.Float(
        validate=validate.Range(min=1.0, max=10.0),
        load_default=None,
        allow_none=True,
    )

    pros = fields.List(fields.String(validate=validate.Length(max=200)), load_default=[])
    cons = fields.List(fields.String(validate=validate.Length(max=200)), load_default=[])
    award = fields.String(
        validate=validate.OneOf([
            "Editor's Choice", "Best Value", "Best Performance",
            "Best Design", "Best Budget", "Innovation Award",
        ]),
        load_default=None,
        allow_none=True,
    )
    is_published = fields.Boolean(load_default=False)


class TechReviewUpdateSchema(Schema):
    """Schema for updating a tech review."""
    title = fields.String(validate=validate.Length(min=5, max=300))
    summary = fields.String(validate=validate.Length(min=20, max=2000))
    body = fields.String(validate=validate.Length(min=100))
    verdict = fields.String(validate=validate.Length(min=20, max=2000))

    score_performance = fields.Float(validate=validate.Range(min=1.0, max=10.0))
    score_value = fields.Float(validate=validate.Range(min=1.0, max=10.0))
    score_design = fields.Float(validate=validate.Range(min=1.0, max=10.0))
    score_features = fields.Float(validate=validate.Range(min=1.0, max=10.0))
    score_battery = fields.Float(
        validate=validate.Range(min=1.0, max=10.0),
        allow_none=True,
    )

    pros = fields.List(fields.String(validate=validate.Length(max=200)))
    cons = fields.List(fields.String(validate=validate.Length(max=200)))
    award = fields.String(allow_none=True)
    is_published = fields.Boolean()


class ReviewFilterSchema(Schema):
    """Schema for review listing query parameters."""
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))
    rating = fields.Integer(validate=validate.Range(min=1, max=5), load_default=None)
    verified_only = fields.Boolean(load_default=False)
    sort = fields.String(
        load_default="created_at",
        validate=validate.OneOf(["created_at", "rating", "helpful_count"]),
    )
    order = fields.String(
        load_default="desc",
        validate=validate.OneOf(["asc", "desc"]),
    )
