"""
WarrantyRegistration Model
"""
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from ..extensions import db


class WarrantyRegistration(db.Model):
    """Product warranty registration and claims."""

    __tablename__ = "warranty_registrations"

    STATUS_ACTIVE = "active"
    STATUS_EXPIRED = "expired"
    STATUS_CLAIMED = "claimed"
    STATUS_VOID = "void"

    CLAIM_STATUS_NONE = "none"
    CLAIM_STATUS_SUBMITTED = "submitted"
    CLAIM_STATUS_IN_REVIEW = "in_review"
    CLAIM_STATUS_APPROVED = "approved"
    CLAIM_STATUS_REJECTED = "rejected"
    CLAIM_STATUS_RESOLVED = "resolved"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    order_item_id = db.Column(db.Integer, db.ForeignKey("order_items.id"), nullable=True)

    serial_number = db.Column(db.String(100), nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    warranty_start = db.Column(db.Date, nullable=False)
    warranty_end = db.Column(db.Date, nullable=False)

    status = db.Column(db.String(20), nullable=False, default=STATUS_ACTIVE)

    # Claim fields
    claim_status = db.Column(db.String(20), nullable=False, default=CLAIM_STATUS_NONE)
    claim_description = db.Column(db.Text, nullable=True)
    claim_submitted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    claim_resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    claim_resolution_notes = db.Column(db.Text, nullable=True)

    # Reminder tracking
    reminder_sent = db.Column(db.Boolean, default=False)
    reminder_sent_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = db.relationship("User", back_populates="warranties")
    product = db.relationship("Product")
    order_item = db.relationship("OrderItem")

    @property
    def is_expired(self) -> bool:
        return self.warranty_end < datetime.now(timezone.utc).date()

    @property
    def days_remaining(self) -> int:
        delta = self.warranty_end - datetime.now(timezone.utc).date()
        return max(delta.days, 0)

    @property
    def has_active_claim(self) -> bool:
        return self.claim_status in (
            self.CLAIM_STATUS_SUBMITTED,
            self.CLAIM_STATUS_IN_REVIEW,
        )

    @staticmethod
    def create_from_order_item(user_id: int, order_item, serial_number: str) -> "WarrantyRegistration":
        """Create a warranty registration from a completed order item."""
        product = order_item.product
        purchase_date = order_item.order.created_at.date()
        warranty_start = purchase_date
        warranty_end = purchase_date + relativedelta(months=product.warranty_months)

        registration = WarrantyRegistration(
            user_id=user_id,
            product_id=product.id,
            order_item_id=order_item.id,
            serial_number=serial_number,
            purchase_date=purchase_date,
            warranty_start=warranty_start,
            warranty_end=warranty_end,
            status=WarrantyRegistration.STATUS_ACTIVE,
        )
        return registration

    def submit_claim(self, description: str) -> None:
        """Submit a warranty claim."""
        if self.is_expired:
            raise ValueError("Warranty has expired. Claims cannot be submitted.")
        if self.has_active_claim:
            raise ValueError("An active claim already exists for this warranty.")
        if self.status != self.STATUS_ACTIVE:
            raise ValueError(f"Cannot submit claim for warranty with status '{self.status}'.")

        self.claim_status = self.CLAIM_STATUS_SUBMITTED
        self.claim_description = description
        self.claim_submitted_at = datetime.now(timezone.utc)
        self.status = self.STATUS_CLAIMED

    def resolve_claim(self, resolution_notes: str, approved: bool = True) -> None:
        """Resolve a warranty claim (admin action)."""
        self.claim_status = self.CLAIM_STATUS_APPROVED if approved else self.CLAIM_STATUS_REJECTED
        self.claim_resolution_notes = resolution_notes
        self.claim_resolved_at = datetime.now(timezone.utc)

        if not approved:
            self.status = self.STATUS_ACTIVE if not self.is_expired else self.STATUS_EXPIRED

    def check_and_update_expiry(self) -> bool:
        """Check if warranty has expired and update status. Returns True if newly expired."""
        if self.status == self.STATUS_ACTIVE and self.is_expired:
            self.status = self.STATUS_EXPIRED
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "serial_number": self.serial_number,
            "purchase_date": self.purchase_date.isoformat() if self.purchase_date else None,
            "warranty_start": self.warranty_start.isoformat() if self.warranty_start else None,
            "warranty_end": self.warranty_end.isoformat() if self.warranty_end else None,
            "status": self.status,
            "days_remaining": self.days_remaining,
            "claim": {
                "status": self.claim_status,
                "description": self.claim_description,
                "submitted_at": self.claim_submitted_at.isoformat() if self.claim_submitted_at else None,
                "resolved_at": self.claim_resolved_at.isoformat() if self.claim_resolved_at else None,
                "resolution_notes": self.claim_resolution_notes,
            } if self.claim_status != self.CLAIM_STATUS_NONE else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<WarrantyRegistration {self.id} ({self.status})>"
