"""
Tests for Order API Endpoints
"""
import json
import pytest
from decimal import Decimal


class TestOrderList:
    """Tests for GET /api/orders"""

    def test_list_orders_authenticated(self, client, auth_headers, sample_order):
        """Authenticated user can list their orders."""
        response = client.get("/api/orders", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_list_orders_unauthenticated(self, client):
        """Unauthenticated request to list orders returns 401."""
        response = client.get("/api/orders")
        assert response.status_code == 401

    def test_list_orders_filter_by_status(self, client, auth_headers, sample_order):
        """Orders can be filtered by status."""
        response = client.get("/api/orders?status=paid", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        for item in data["items"]:
            assert item["status"] == "paid"


class TestOrderCreate:
    """Tests for POST /api/orders"""

    def test_create_order(self, client, auth_headers, sample_product):
        """Authenticated user can place an order."""
        payload = {
            "items": [
                {"product_id": sample_product.id, "quantity": 1}
            ],
            "shipping_address": {
                "first_name": "Test",
                "last_name": "Customer",
                "line1": "456 Order Ave",
                "city": "Commerce City",
                "state": "CC",
                "zip_code": "67890",
            },
            "customer_notes": "Please handle with care.",
        }
        response = client.post(
            "/api/orders",
            data=json.dumps(payload),
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "order" in data
        order = data["order"]
        assert order["status"] == "pending"
        assert len(order["items"]) == 1
        assert order["items"][0]["product_id"] == sample_product.id

    def test_create_order_empty_items(self, client, auth_headers):
        """Creating an order with no items returns 400."""
        payload = {"items": []}
        response = client.post(
            "/api/orders",
            data=json.dumps(payload),
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_create_order_nonexistent_product(self, client, auth_headers):
        """Creating an order with a nonexistent product returns 404."""
        payload = {
            "items": [{"product_id": 999999, "quantity": 1}],
        }
        response = client.post(
            "/api/orders",
            data=json.dumps(payload),
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_create_order_insufficient_stock(self, client, auth_headers, sample_product):
        """Creating an order that exceeds stock returns 400."""
        payload = {
            "items": [{"product_id": sample_product.id, "quantity": 99999}],
        }
        response = client.post(
            "/api/orders",
            data=json.dumps(payload),
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "insufficient stock" in response.get_json()["error"].lower()


class TestOrderDetail:
    """Tests for GET /api/orders/<order_id>"""

    def test_get_own_order(self, client, auth_headers, sample_order):
        """User can view their own order."""
        response = client.get(
            f"/api/orders/{sample_order.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["order"]["id"] == sample_order.id
        assert "items" in data["order"]
        assert "payment" in data["order"]

    def test_get_other_users_order(self, client, admin_headers, sample_order):
        """User cannot view another user's order via the customer endpoint."""
        response = client.get(
            f"/api/orders/{sample_order.id}",
            headers=admin_headers,
        )
        # Admin user didn't create this order, so it returns 404
        assert response.status_code == 404


class TestOrderCancel:
    """Tests for PUT /api/orders/<order_id>/cancel"""

    def test_cancel_pending_order(self, client, db, auth_headers, sample_user, sample_product):
        """User can cancel a pending order."""
        from app.models.order import Order, OrderItem, Payment

        order = Order(
            user_id=sample_user.id,
            status=Order.STATUS_PENDING,
            subtotal=sample_product.price,
            tax_amount=Decimal("50.00"),
            total=sample_product.price + Decimal("50.00"),
        )
        db.session.add(order)
        db.session.flush()

        item = OrderItem(
            order_id=order.id,
            product_id=sample_product.id,
            quantity=1,
            unit_price=sample_product.price,
            product_name=sample_product.name,
            product_sku=sample_product.sku,
        )
        db.session.add(item)
        db.session.commit()

        initial_stock = sample_product.stock_quantity

        response = client.put(
            f"/api/orders/{order.id}/cancel",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["order"]["status"] == "cancelled"

    def test_cancel_shipped_order_fails(self, client, db, auth_headers, sample_user, sample_product):
        """User cannot cancel a shipped order."""
        from app.models.order import Order, OrderItem

        order = Order(
            user_id=sample_user.id,
            status=Order.STATUS_SHIPPED,
            subtotal=Decimal("100.00"),
            total=Decimal("108.00"),
        )
        db.session.add(order)
        db.session.flush()

        item = OrderItem(
            order_id=order.id,
            product_id=sample_product.id,
            quantity=1,
            unit_price=Decimal("100.00"),
            product_name="Product",
            product_sku="SKU-001",
        )
        db.session.add(item)
        db.session.commit()

        response = client.put(
            f"/api/orders/{order.id}/cancel",
            headers=auth_headers,
        )
        assert response.status_code == 400
