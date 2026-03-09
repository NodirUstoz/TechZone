"""
Warranty API Endpoints
"""
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, current_user
from marshmallow import Schema, fields, validate

from ..extensions import db
from ..models.warranty import WarrantyRegistration
from ..models.order import Order, OrderItem
from ..utils.pagination import paginate_query


class WarrantyCreateSchema(Schema):
    order_item_id = fields.Integer(required=True)
    serial_number = fields.String(required=True, validate=validate.Length(min=3, max=100))


class WarrantyClaimSchema(Schema):
    description = fields.String(required=True, validate=validate.Length(min=10, max=2000))


class WarrantyListResource(Resource):
    """GET /api/warranties  |  POST"""

    @jwt_required()
    def get(self):
        query = WarrantyRegistration.query.filter_by(user_id=current_user.id).order_by(
            WarrantyRegistration.created_at.desc()
        )

        status = request.args.get("status")
        if status:
            query = query.filter_by(status=status)

        return paginate_query(query, lambda w: w.to_dict())

    @jwt_required()
    def post(self):
        schema = WarrantyCreateSchema()
        errors = schema.validate(request.json or {})
        if errors:
            return {"error": "Validation failed", "details": errors}, 400

        data = schema.load(request.json)

        # Verify the order item belongs to the user and order is delivered
        order_item = OrderItem.query.get(data["order_item_id"])
        if not order_item:
            return {"error": "Order item not found."}, 404

        order = order_item.order
        if order.user_id != current_user.id:
            return {"error": "Order item not found."}, 404

        if order.status not in ("delivered", "shipped"):
            return {"error": "Warranty can only be registered for delivered orders."}, 400

        # Check for duplicate warranty
        existing = WarrantyRegistration.query.filter_by(
            user_id=current_user.id,
            order_item_id=data["order_item_id"],
        ).first()
        if existing:
            return {"error": "Warranty already registered for this item."}, 409

        registration = WarrantyRegistration.create_from_order_item(
            user_id=current_user.id,
            order_item=order_item,
            serial_number=data["serial_number"],
        )

        db.session.add(registration)
        db.session.commit()

        return {"message": "Warranty registered.", "warranty": registration.to_dict()}, 201


class WarrantyDetailResource(Resource):
    """GET /api/warranties/<warranty_id>"""

    @jwt_required()
    def get(self, warranty_id):
        warranty = WarrantyRegistration.query.get_or_404(warranty_id)
        if warranty.user_id != current_user.id and not current_user.is_admin:
            return {"error": "Not authorized."}, 403

        # Auto-check expiry
        warranty.check_and_update_expiry()
        db.session.commit()

        return {"warranty": warranty.to_dict()}, 200


class WarrantyClaimResource(Resource):
    """POST /api/warranties/<warranty_id>/claim"""

    @jwt_required()
    def post(self, warranty_id):
        warranty = WarrantyRegistration.query.get_or_404(warranty_id)
        if warranty.user_id != current_user.id:
            return {"error": "Not authorized."}, 403

        schema = WarrantyClaimSchema()
        errors = schema.validate(request.json or {})
        if errors:
            return {"error": "Validation failed", "details": errors}, 400

        data = schema.load(request.json)

        try:
            warranty.submit_claim(data["description"])
            db.session.commit()
        except ValueError as e:
            return {"error": str(e)}, 400

        return {"message": "Warranty claim submitted.", "warranty": warranty.to_dict()}, 200
