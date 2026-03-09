"""
PriceAlert and PriceHistory Models
"""
from datetime import datetime, timezone

from ..extensions import db


class PriceAlert(db.Model):
    """User-defined price alert for a product."""

    __tablename__ = "price_alerts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    target_price = db.Column(db.Numeric(10, 2), nullable=False)
    is_triggered = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    triggered_at = db.Column(db.DateTime(timezone=True), nullable=True)
    notified_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # One active alert per user per product
    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="uq_price_alert_user_product"),
    )

    # Relationships
    user = db.relationship("User", back_populates="price_alerts")
    product = db.relationship("Product", back_populates="price_alerts")

    def trigger(self) -> None:
        """Mark the alert as triggered."""
        self.is_triggered = True
        self.triggered_at = datetime.now(timezone.utc)
        self.is_active = False

    def mark_notified(self) -> None:
        """Record that the user has been notified."""
        self.notified_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "current_price": float(self.product.price) if self.product else None,
            "target_price": float(self.target_price),
            "is_triggered": self.is_triggered,
            "is_active": self.is_active,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<PriceAlert product={self.product_id} target={self.target_price}>"


class PriceHistory(db.Model):
    """Historical price record for a product."""

    __tablename__ = "price_history"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    price = db.Column(db.Numeric(10, 2), nullable=False)
    source = db.Column(db.String(50), nullable=True, default="internal")  # internal, scraper, manual
    recorded_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # Relationship
    product = db.relationship("Product", back_populates="price_history")

    @staticmethod
    def record_price(product_id: int, price: float, source: str = "internal") -> "PriceHistory":
        """Create a new price history entry."""
        entry = PriceHistory(
            product_id=product_id,
            price=price,
            source=source,
        )
        db.session.add(entry)
        return entry

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "price": float(self.price),
            "source": self.source,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }

    def __repr__(self) -> str:
        return f"<PriceHistory product={self.product_id} price={self.price}>"
