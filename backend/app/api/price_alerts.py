"""
Price Alert and Price History API Endpoints
"""
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, current_user
from marshmallow import Schema, fields, validate

from ..extensions import db
from ..models.price_alert import PriceAlert, PriceHistory
from ..models.product import Product
from ..utils.pagination import paginate_query


class PriceAlertCreateSchema(Schema):
    product_id = fields.Integer(required=True)
    target_price = fields.Float(required=True, validate=validate.Range(min=0.01))


class PriceAlertListResource(Resource):
    """GET /api/price-alerts  |  POST"""

    @jwt_required()
    def get(self):
        query = PriceAlert.query.filter_by(user_id=current_user.id).order_by(PriceAlert.created_at.desc())

        # Filter by active/triggered
        active_only = request.args.get("active", "").lower() == "true"
        if active_only:
            query = query.filter_by(is_active=True)

        return paginate_query(query, lambda a: a.to_dict())

    @jwt_required()
    def post(self):
        schema = PriceAlertCreateSchema()
        errors = schema.validate(request.json or {})
        if errors:
            return {"error": "Validation failed", "details": errors}, 400

        data = schema.load(request.json)
        product = Product.query.get(data["product_id"])
        if not product:
            return {"error": "Product not found."}, 404

        # Check if alert already exists for this user + product
        existing = PriceAlert.query.filter_by(
            user_id=current_user.id,
            product_id=data["product_id"],
        ).first()

        if existing and existing.is_active:
            return {"error": "You already have an active price alert for this product."}, 409

        # If previous alert was triggered, replace it
        if existing:
            existing.target_price = data["target_price"]
            existing.is_active = True
            existing.is_triggered = False
            existing.triggered_at = None
            existing.notified_at = None
            alert = existing
        else:
            alert = PriceAlert(
                user_id=current_user.id,
                product_id=data["product_id"],
                target_price=data["target_price"],
            )
            db.session.add(alert)

        db.session.commit()

        # Immediately check if target is already met
        if product.price <= alert.target_price:
            alert.trigger()
            db.session.commit()
            return {
                "message": "Price alert triggered immediately -- the current price already meets your target.",
                "alert": alert.to_dict(),
            }, 201

        return {"message": "Price alert created.", "alert": alert.to_dict()}, 201


class PriceAlertDetailResource(Resource):
    """DELETE /api/price-alerts/<alert_id>"""

    @jwt_required()
    def delete(self, alert_id):
        alert = PriceAlert.query.get_or_404(alert_id)
        if alert.user_id != current_user.id:
            return {"error": "Not authorized."}, 403

        db.session.delete(alert)
        db.session.commit()
        return {"message": "Price alert deleted."}, 200


class PriceHistoryResource(Resource):
    """GET /api/products/<product_id>/price-history"""

    def get(self, product_id):
        Product.query.get_or_404(product_id)

        days = request.args.get("days", 90, type=int)
        limit = min(request.args.get("limit", 500, type=int), 1000)

        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        history = (
            PriceHistory.query
            .filter(
                PriceHistory.product_id == product_id,
                PriceHistory.recorded_at >= cutoff,
            )
            .order_by(PriceHistory.recorded_at.asc())
            .limit(limit)
            .all()
        )

        prices = [float(h.price) for h in history]
        stats = {}
        if prices:
            stats = {
                "min": min(prices),
                "max": max(prices),
                "average": round(sum(prices) / len(prices), 2),
                "current": prices[-1],
                "data_points": len(prices),
            }

        return {
            "product_id": product_id,
            "history": [h.to_dict() for h in history],
            "stats": stats,
        }, 200
