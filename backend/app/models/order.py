"""
Order, OrderItem, and Payment Models
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from ..extensions import db


class Order(db.Model):
    """Customer order."""

    __tablename__ = "orders"

    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_PROCESSING = "processing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    VALID_STATUSES = [
        STATUS_PENDING, STATUS_PAID, STATUS_PROCESSING,
        STATUS_SHIPPED, STATUS_DELIVERED, STATUS_CANCELLED,
    ]

    CANCELLABLE_STATUSES = [STATUS_PENDING, STATUS_PAID]

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())[:12].upper())
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Status
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDING)

    # Pricing
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    shipping_amount = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    discount_amount = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    total = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    # Shipping address snapshot (stored at order time)
    shipping_first_name = db.Column(db.String(100), nullable=True)
    shipping_last_name = db.Column(db.String(100), nullable=True)
    shipping_address_line1 = db.Column(db.String(255), nullable=True)
    shipping_address_line2 = db.Column(db.String(255), nullable=True)
    shipping_city = db.Column(db.String(100), nullable=True)
    shipping_state = db.Column(db.String(100), nullable=True)
    shipping_zip_code = db.Column(db.String(20), nullable=True)
    shipping_country = db.Column(db.String(100), nullable=True, default="US")

    # Tracking
    tracking_number = db.Column(db.String(100), nullable=True)
    shipping_carrier = db.Column(db.String(50), nullable=True)

    # Notes
    customer_notes = db.Column(db.Text, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    shipped_at = db.Column(db.DateTime(timezone=True), nullable=True)
    delivered_at = db.Column(db.DateTime(timezone=True), nullable=True)
    cancelled_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    user = db.relationship("User", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", lazy="joined", cascade="all, delete-orphan")
    payment = db.relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")

    @property
    def is_cancellable(self) -> bool:
        return self.status in self.CANCELLABLE_STATUSES

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)

    def calculate_totals(self, tax_rate: Decimal = Decimal("0.08")) -> None:
        """Recalculate order totals from items."""
        self.subtotal = sum(item.line_total for item in self.items)
        self.tax_amount = (self.subtotal * tax_rate).quantize(Decimal("0.01"))
        self.total = self.subtotal + self.tax_amount + self.shipping_amount - self.discount_amount

    def cancel(self) -> None:
        """Cancel the order and restore stock."""
        if not self.is_cancellable:
            raise ValueError(f"Cannot cancel order in '{self.status}' status.")
        self.status = self.STATUS_CANCELLED
        self.cancelled_at = datetime.now(timezone.utc)
        for item in self.items:
            if item.product:
                item.product.stock_quantity += item.quantity

    def to_dict(self, include_items: bool = True) -> dict:
        data = {
            "id": self.id,
            "order_number": self.order_number,
            "user_id": self.user_id,
            "status": self.status,
            "subtotal": float(self.subtotal),
            "tax_amount": float(self.tax_amount),
            "shipping_amount": float(self.shipping_amount),
            "discount_amount": float(self.discount_amount),
            "total": float(self.total),
            "item_count": self.item_count,
            "tracking_number": self.tracking_number,
            "shipping_carrier": self.shipping_carrier,
            "customer_notes": self.customer_notes,
            "shipping_address": {
                "first_name": self.shipping_first_name,
                "last_name": self.shipping_last_name,
                "line1": self.shipping_address_line1,
                "line2": self.shipping_address_line2,
                "city": self.shipping_city,
                "state": self.shipping_state,
                "zip_code": self.shipping_zip_code,
                "country": self.shipping_country,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "shipped_at": self.shipped_at.isoformat() if self.shipped_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        if self.payment:
            data["payment"] = self.payment.to_dict()
        return data

    def __repr__(self) -> str:
        return f"<Order {self.order_number} ({self.status})>"


class OrderItem(db.Model):
    """Single line item in an order."""

    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    # Price snapshot at time of purchase
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    product_sku = db.Column(db.String(50), nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "product_sku": self.product_sku,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "line_total": float(self.line_total),
            "product_image": self.product.primary_image_url if self.product else None,
        }

    def __repr__(self) -> str:
        return f"<OrderItem {self.product_name} x{self.quantity}>"


class Payment(db.Model):
    """Payment record for an order."""

    __tablename__ = "payments"

    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_REFUNDED = "refunded"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Stripe integration
    stripe_payment_intent_id = db.Column(db.String(255), nullable=True, unique=True)
    stripe_charge_id = db.Column(db.String(255), nullable=True)

    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), default="USD", nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDING)
    payment_method = db.Column(db.String(50), nullable=True)  # card, paypal, etc.

    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    order = db.relationship("Order", back_populates="payment")

    def mark_completed(self) -> None:
        self.status = self.STATUS_COMPLETED
        self.completed_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "amount": float(self.amount),
            "currency": self.currency,
            "status": self.status,
            "payment_method": self.payment_method,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self) -> str:
        return f"<Payment {self.id} ({self.status})>"
