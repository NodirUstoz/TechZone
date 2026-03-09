"""
Order Service
"""
from decimal import Decimal
from typing import Optional

from ..extensions import db
from ..models.order import Order, OrderItem, Payment
from ..models.user import User


class OrderService:
    """Business logic for order management."""

    TAX_RATE = Decimal("0.08")  # 8% sales tax
    FREE_SHIPPING_THRESHOLD = Decimal("99.00")
    FLAT_SHIPPING_RATE = Decimal("9.99")

    @staticmethod
    def create_order(
        user: User,
        items: list[dict],
        shipping_address: Optional[dict] = None,
        customer_notes: Optional[str] = None,
    ) -> Order:
        """
        Create a new order from a list of items.

        Args:
            user: The user placing the order.
            items: List of dicts with 'product' and 'quantity'.
            shipping_address: Optional shipping address override.
            customer_notes: Optional customer notes.

        Returns:
            The created Order.
        """
        order = Order(
            user_id=user.id,
            customer_notes=customer_notes,
        )

        # Set shipping address (from request data or user profile)
        addr = shipping_address or {}
        order.shipping_first_name = addr.get("first_name", user.first_name)
        order.shipping_last_name = addr.get("last_name", user.last_name)
        order.shipping_address_line1 = addr.get("line1", user.address_line1)
        order.shipping_address_line2 = addr.get("line2", user.address_line2)
        order.shipping_city = addr.get("city", user.city)
        order.shipping_state = addr.get("state", user.state)
        order.shipping_zip_code = addr.get("zip_code", user.zip_code)
        order.shipping_country = addr.get("country", user.country or "US")

        db.session.add(order)
        db.session.flush()

        # Create order items and deduct stock
        for item_data in items:
            product = item_data["product"]
            quantity = item_data["quantity"]

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price,
                product_name=product.name,
                product_sku=product.sku,
            )
            db.session.add(order_item)
            order.items.append(order_item)

            # Deduct stock
            product.stock_quantity -= quantity

        # Calculate shipping
        subtotal = sum(item.line_total for item in order.items)
        if subtotal >= OrderService.FREE_SHIPPING_THRESHOLD:
            order.shipping_amount = Decimal("0.00")
        else:
            order.shipping_amount = OrderService.FLAT_SHIPPING_RATE

        # Calculate totals
        order.calculate_totals(tax_rate=OrderService.TAX_RATE)

        # Create pending payment record
        payment = Payment(
            order_id=order.id,
            amount=order.total,
            currency="USD",
            status=Payment.STATUS_PENDING,
        )
        db.session.add(payment)

        db.session.commit()
        return order

    @staticmethod
    def process_payment(order: Order, stripe_payment_intent_id: str, payment_method: str = "card") -> Payment:
        """
        Mark payment as completed and advance order status.

        Args:
            order: The order to process payment for.
            stripe_payment_intent_id: Stripe PaymentIntent ID.
            payment_method: Payment method type.

        Returns:
            The updated Payment.
        """
        payment = order.payment
        if not payment:
            raise ValueError("No payment record found for this order.")

        payment.stripe_payment_intent_id = stripe_payment_intent_id
        payment.payment_method = payment_method
        payment.mark_completed()

        order.status = Order.STATUS_PAID

        db.session.commit()
        return payment

    @staticmethod
    def update_status(order: Order, new_status: str, **kwargs) -> Order:
        """
        Update order status with validation.

        Args:
            order: The order to update.
            new_status: The target status.
            **kwargs: Additional fields (tracking_number, shipping_carrier, etc.).

        Returns:
            The updated Order.
        """
        valid_transitions = {
            Order.STATUS_PENDING: [Order.STATUS_PAID, Order.STATUS_CANCELLED],
            Order.STATUS_PAID: [Order.STATUS_PROCESSING, Order.STATUS_CANCELLED],
            Order.STATUS_PROCESSING: [Order.STATUS_SHIPPED],
            Order.STATUS_SHIPPED: [Order.STATUS_DELIVERED],
            Order.STATUS_DELIVERED: [],
            Order.STATUS_CANCELLED: [],
        }

        allowed = valid_transitions.get(order.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from '{order.status}' to '{new_status}'. "
                f"Allowed transitions: {allowed}"
            )

        order.status = new_status

        if new_status == Order.STATUS_SHIPPED:
            from datetime import datetime, timezone
            order.shipped_at = datetime.now(timezone.utc)
            order.tracking_number = kwargs.get("tracking_number", order.tracking_number)
            order.shipping_carrier = kwargs.get("shipping_carrier", order.shipping_carrier)
        elif new_status == Order.STATUS_DELIVERED:
            from datetime import datetime, timezone
            order.delivered_at = datetime.now(timezone.utc)
        elif new_status == Order.STATUS_CANCELLED:
            order.cancel()

        db.session.commit()
        return order

    @staticmethod
    def get_order_stats(user_id: int) -> dict:
        """Get order statistics for a user."""
        from sqlalchemy import func

        total_orders = Order.query.filter_by(user_id=user_id).count()
        total_spent = db.session.query(func.sum(Order.total)).filter(
            Order.user_id == user_id,
            Order.status.notin_(["cancelled"]),
        ).scalar() or 0

        return {
            "total_orders": total_orders,
            "total_spent": float(total_spent),
        }
