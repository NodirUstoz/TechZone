"""
Comparison List API Endpoints
"""
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, current_user
from marshmallow import Schema, fields, validate

from ..extensions import db
from ..models.comparison import ComparisonList
from ..models.product import Product


class ComparisonCreateSchema(Schema):
    name = fields.String(load_default="My Comparison", validate=validate.Length(min=1, max=200))
    product_ids = fields.List(fields.Integer(), load_default=[])


class ComparisonListResource(Resource):
    """GET /api/comparisons  |  POST"""

    @jwt_required()
    def get(self):
        comparisons = ComparisonList.query.filter_by(user_id=current_user.id).order_by(
            ComparisonList.updated_at.desc()
        ).all()
        return {
            "comparisons": [c.to_dict() for c in comparisons]
        }, 200

    @jwt_required()
    def post(self):
        schema = ComparisonCreateSchema()
        errors = schema.validate(request.json or {})
        if errors:
            return {"error": "Validation failed", "details": errors}, 400

        data = schema.load(request.json)

        comparison = ComparisonList(
            user_id=current_user.id,
            name=data["name"],
        )
        db.session.add(comparison)
        db.session.flush()

        # Add initial products
        for pid in data.get("product_ids", []):
            product = Product.query.get(pid)
            if product:
                try:
                    comparison.add_product(product)
                except ValueError as e:
                    db.session.rollback()
                    return {"error": str(e)}, 400

        db.session.commit()

        return {"message": "Comparison list created.", "comparison": comparison.to_dict()}, 201


class ComparisonDetailResource(Resource):
    """GET /api/comparisons/<comparison_id>  |  DELETE"""

    def get(self, comparison_id):
        # Allow public access via share token
        share_token = request.args.get("token")
        if share_token:
            comparison = ComparisonList.query.filter_by(
                id=comparison_id, share_token=share_token, is_public=True
            ).first_or_404()
        else:
            comparison = ComparisonList.query.get_or_404(comparison_id)

        return {"comparison": comparison.to_dict(include_comparison=True)}, 200

    @jwt_required()
    def delete(self, comparison_id):
        comparison = ComparisonList.query.get_or_404(comparison_id)
        if comparison.user_id != current_user.id:
            return {"error": "Not authorized."}, 403

        db.session.delete(comparison)
        db.session.commit()
        return {"message": "Comparison list deleted."}, 200


class ComparisonProductsResource(Resource):
    """PUT /api/comparisons/<comparison_id>/products  (add/remove products)"""

    @jwt_required()
    def put(self, comparison_id):
        comparison = ComparisonList.query.get_or_404(comparison_id)
        if comparison.user_id != current_user.id:
            return {"error": "Not authorized."}, 403

        data = request.json or {}
        action = data.get("action")  # "add" or "remove"
        product_id = data.get("product_id")

        if not action or not product_id:
            return {"error": "Both 'action' (add/remove) and 'product_id' are required."}, 400

        product = Product.query.get(product_id)
        if not product:
            return {"error": "Product not found."}, 404

        try:
            if action == "add":
                comparison.add_product(product)
            elif action == "remove":
                comparison.remove_product(product)
            else:
                return {"error": "Invalid action. Use 'add' or 'remove'."}, 400
        except ValueError as e:
            return {"error": str(e)}, 400

        db.session.commit()

        return {
            "message": f"Product {'added to' if action == 'add' else 'removed from'} comparison.",
            "comparison": comparison.to_dict(include_comparison=True),
        }, 200

    @jwt_required()
    def post(self, comparison_id):
        """Generate a shareable link."""
        comparison = ComparisonList.query.get_or_404(comparison_id)
        if comparison.user_id != current_user.id:
            return {"error": "Not authorized."}, 403

        token = comparison.generate_share_token()
        db.session.commit()

        return {
            "message": "Share link generated.",
            "share_token": token,
            "share_url": f"/comparisons/{comparison.id}?token={token}",
        }, 200
