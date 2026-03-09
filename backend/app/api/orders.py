"""
Order API Endpoints
"""
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, current_user

from ..extensions import db
from ..models.order import Order, OrderItem, Payment
from ..models.product import Product
from ..schemas.order_schema import OrderCreateSchema
from ..services.order_service import OrderService
from ..utils.pagination import paginate_query


class OrderListResource(Resource):
    """GET /api/orders  |  POST /api/orders"""

    @jwt_required()
    def get(self):
        query = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc())

        # Optional status filter
        status = request.args.get("status")
        if status and status in Order.VALID_STATUSES:
            query = query.filter_by(status=status)

        return paginate_query(query, lambda o: o.to_dict())

    @jwt_required()
    def post(self):
        schema = OrderCreateSchema()
        errors = schema.validate(request.json or {})
        if errors:
            return {"error": "Validation failed", "details": errors}, 400

        data = schema.load(request.json)
        items_data = data.get("items", [])

        if not items_data:
            return {"error": "Order must contain at least one item."}, 400

        # Validate products and stock
        order_items = []
        for item_data in items_data:
            product = Product.query.get(item_data["product_id"])
            if not product:
                return {"error": f"Product {item_data['product_id']} not found."}, 404
            if not product.is_active:
                return {"error": f"Product '{product.name}' is no longer available."}, 400
            if product.stock_quantity < item_data["quantity"]:
                return {
                    "error": f"Insufficient stock for '{product.name}'. Available: {product.stock_quantity}."
                }, 400
            order_items.append({
                "product": product,
                "quantity": item_data["quantity"],
            })

        # Create the order
        order = OrderService.create_order(
            user=current_user,
            items=order_items,
            shipping_address=data.get("shipping_address"),
            customer_notes=data.get("customer_notes"),
        )

        return {"message": "Order placed successfully.", "order": order.to_dict()}, 201


class OrderDetailResource(Resource):
    """GET /api/orders/<order_id>"""

    @jwt_required()
    def get(self, order_id):
        order = Order.query.get_or_404(order_id)

        # Users can only view their own orders (admins handled via admin endpoint)
        if order.user_id != current_user.id:
            return {"error": "Order not found."}, 404

        return {"order": order.to_dict()}, 200


class OrderCancelResource(Resource):
    """PUT /api/orders/<order_id>/cancel"""

    @jwt_required()
    def put(self, order_id):
        order = Order.query.get_or_404(order_id)

        if order.user_id != current_user.id:
            return {"error": "Order not found."}, 404

        if not order.is_cancellable:
            return {"error": f"Order in '{order.status}' status cannot be cancelled."}, 400

        try:
            order.cancel()
            db.session.commit()
        except ValueError as e:
            return {"error": str(e)}, 400

        return {"message": "Order cancelled.", "order": order.to_dict()}, 200
