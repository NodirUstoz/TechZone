"""
Admin API Endpoints
"""
from datetime import datetime, timezone, timedelta

from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models.user import User
from ..models.product import Product
from ..models.order import Order
from ..models.review import Review
from ..utils.decorators import admin_required
from ..utils.pagination import paginate_query


class AdminDashboardResource(Resource):
    """GET /api/admin/dashboard"""

    @jwt_required()
    @admin_required
    def get(self):
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)

        # User stats
        total_users = User.query.count()
        new_users_30d = User.query.filter(User.created_at >= thirty_days_ago).count()

        # Product stats
        total_products = Product.query.filter_by(is_active=True).count()
        low_stock = Product.query.filter(
            Product.is_active == True,
            Product.stock_quantity > 0,
            Product.stock_quantity <= Product.low_stock_threshold,
        ).count()
        out_of_stock = Product.query.filter(
            Product.is_active == True,
            Product.stock_quantity == 0,
        ).count()

        # Order stats
        total_orders = Order.query.count()
        orders_30d = Order.query.filter(Order.created_at >= thirty_days_ago).count()
        orders_7d = Order.query.filter(Order.created_at >= seven_days_ago).count()

        pending_orders = Order.query.filter_by(status=Order.STATUS_PENDING).count()
        processing_orders = Order.query.filter_by(status=Order.STATUS_PROCESSING).count()

        # Revenue
        from sqlalchemy import func
        revenue_30d = db.session.query(func.sum(Order.total)).filter(
            Order.created_at >= thirty_days_ago,
            Order.status.notin_(["cancelled"]),
        ).scalar() or 0

        revenue_total = db.session.query(func.sum(Order.total)).filter(
            Order.status.notin_(["cancelled"]),
        ).scalar() or 0

        # Review stats
        total_reviews = Review.query.count()
        pending_reviews = Review.query.filter_by(is_approved=False).count()

        # Recent orders
        recent_orders = (
            Order.query
            .order_by(Order.created_at.desc())
            .limit(10)
            .all()
        )

        return {
            "dashboard": {
                "users": {
                    "total": total_users,
                    "new_30d": new_users_30d,
                },
                "products": {
                    "total": total_products,
                    "low_stock": low_stock,
                    "out_of_stock": out_of_stock,
                },
                "orders": {
                    "total": total_orders,
                    "last_30d": orders_30d,
                    "last_7d": orders_7d,
                    "pending": pending_orders,
                    "processing": processing_orders,
                },
                "revenue": {
                    "last_30d": float(revenue_30d),
                    "total": float(revenue_total),
                },
                "reviews": {
                    "total": total_reviews,
                    "pending_approval": pending_reviews,
                },
                "recent_orders": [o.to_dict(include_items=False) for o in recent_orders],
            }
        }, 200


class AdminUsersResource(Resource):
    """GET /api/admin/users"""

    @jwt_required()
    @admin_required
    def get(self):
        query = User.query.order_by(User.created_at.desc())

        role = request.args.get("role")
        if role:
            query = query.filter_by(role=role)

        search = request.args.get("search", "").strip()
        if search:
            query = query.filter(
                db.or_(
                    User.email.ilike(f"%{search}%"),
                    User.username.ilike(f"%{search}%"),
                    User.first_name.ilike(f"%{search}%"),
                    User.last_name.ilike(f"%{search}%"),
                )
            )

        return paginate_query(query, lambda u: u.to_dict(include_private=True))


class AdminUserDetailResource(Resource):
    """PUT /api/admin/users/<user_id>"""

    @jwt_required()
    @admin_required
    def put(self, user_id):
        user = User.query.get_or_404(user_id)
        data = request.json or {}

        if "role" in data and data["role"] in ("customer", "admin"):
            user.role = data["role"]

        if "is_active" in data:
            user.is_active = bool(data["is_active"])

        db.session.commit()
        return {"message": "User updated.", "user": user.to_dict(include_private=True)}, 200

    @jwt_required()
    @admin_required
    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        user_data = user.to_dict(include_private=True)

        # Include order and review counts
        user_data["order_count"] = user.orders.count()
        user_data["review_count"] = user.reviews.count()

        return {"user": user_data}, 200


class AdminOrdersResource(Resource):
    """GET /api/admin/orders"""

    @jwt_required()
    @admin_required
    def get(self):
        query = Order.query.order_by(Order.created_at.desc())

        status = request.args.get("status")
        if status and status in Order.VALID_STATUSES:
            query = query.filter_by(status=status)

        return paginate_query(query, lambda o: o.to_dict())


class AdminOrderDetailResource(Resource):
    """PUT /api/admin/orders/<order_id>"""

    @jwt_required()
    @admin_required
    def put(self, order_id):
        order = Order.query.get_or_404(order_id)
        data = request.json or {}

        new_status = data.get("status")
        if new_status and new_status in Order.VALID_STATUSES:
            if new_status == Order.STATUS_SHIPPED:
                order.tracking_number = data.get("tracking_number", order.tracking_number)
                order.shipping_carrier = data.get("shipping_carrier", order.shipping_carrier)
                order.shipped_at = datetime.now(timezone.utc)
            elif new_status == Order.STATUS_DELIVERED:
                order.delivered_at = datetime.now(timezone.utc)
            elif new_status == Order.STATUS_CANCELLED:
                if not order.is_cancellable:
                    return {"error": f"Cannot cancel order in '{order.status}' status."}, 400
                order.cancel()

            order.status = new_status

        if "admin_notes" in data:
            order.admin_notes = data["admin_notes"]

        db.session.commit()
        return {"message": "Order updated.", "order": order.to_dict()}, 200
