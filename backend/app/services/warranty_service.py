"""
Warranty Service
"""
from datetime import date, datetime, timezone
from typing import Optional

from dateutil.relativedelta import relativedelta

from ..extensions import db
from ..models.warranty import WarrantyRegistration
from ..models.product import Product
from ..models.order import OrderItem


class WarrantyService:
    """Business logic for warranty registration and claims."""

    @staticmethod
    def register_warranty(
        user_id: int,
        product_id: int,
        serial_number: str,
        purchase_date: date,
        order_item_id: Optional[int] = None,
    ) -> WarrantyRegistration:
        """
        Register a product warranty.

        Args:
            user_id: ID of the user registering the warranty.
            product_id: ID of the product.
            serial_number: Product serial number.
            purchase_date: Date the product was purchased.
            order_item_id: Optional link to order item.

        Returns:
            The created WarrantyRegistration.

        Raises:
            ValueError: If the product is not found or a duplicate registration exists.
        """
        product = Product.query.get(product_id)
        if not product:
            raise ValueError("Product not found.")

        # Check for duplicate serial number registration
        existing = WarrantyRegistration.query.filter_by(
            serial_number=serial_number,
            product_id=product_id,
        ).first()
        if existing:
            raise ValueError(
                "A warranty is already registered for this product with this serial number."
            )

        # Validate order item belongs to user if provided
        if order_item_id:
            order_item = OrderItem.query.get(order_item_id)
            if not order_item:
                raise ValueError("Order item not found.")
            if order_item.order.user_id != user_id:
                raise ValueError("Order item does not belong to this user.")
            if order_item.product_id != product_id:
                raise ValueError("Order item does not match the specified product.")

        warranty_start = purchase_date
        warranty_end = purchase_date + relativedelta(months=product.warranty_months)

        registration = WarrantyRegistration(
            user_id=user_id,
            product_id=product_id,
            order_item_id=order_item_id,
            serial_number=serial_number,
            purchase_date=purchase_date,
            warranty_start=warranty_start,
            warranty_end=warranty_end,
            status=WarrantyRegistration.STATUS_ACTIVE,
        )

        # Check if already expired at registration
        if warranty_end < date.today():
            registration.status = WarrantyRegistration.STATUS_EXPIRED

        db.session.add(registration)
        db.session.commit()
        return registration

    @staticmethod
    def submit_claim(warranty_id: int, user_id: int, description: str) -> WarrantyRegistration:
        """
        Submit a warranty claim.

        Args:
            warranty_id: ID of the warranty registration.
            user_id: ID of the claiming user (must match warranty owner).
            description: Claim description.

        Returns:
            The updated WarrantyRegistration.

        Raises:
            ValueError: If claim cannot be submitted.
        """
        warranty = WarrantyRegistration.query.get(warranty_id)
        if not warranty:
            raise ValueError("Warranty registration not found.")
        if warranty.user_id != user_id:
            raise ValueError("This warranty does not belong to you.")

        warranty.submit_claim(description)
        db.session.commit()
        return warranty

    @staticmethod
    def resolve_claim(
        warranty_id: int,
        approved: bool,
        resolution_notes: str,
    ) -> WarrantyRegistration:
        """
        Resolve a warranty claim (admin action).

        Args:
            warranty_id: ID of the warranty registration.
            approved: Whether to approve the claim.
            resolution_notes: Admin resolution notes.

        Returns:
            The updated WarrantyRegistration.

        Raises:
            ValueError: If warranty has no active claim.
        """
        warranty = WarrantyRegistration.query.get(warranty_id)
        if not warranty:
            raise ValueError("Warranty registration not found.")
        if not warranty.has_active_claim:
            raise ValueError("No active claim exists for this warranty.")

        warranty.resolve_claim(resolution_notes, approved=approved)
        db.session.commit()
        return warranty

    @staticmethod
    def check_expiring_warranties(days_ahead: int = 30) -> list[WarrantyRegistration]:
        """
        Find all warranties expiring within the specified number of days.

        Args:
            days_ahead: Number of days to look ahead.

        Returns:
            List of warranties expiring soon.
        """
        today = date.today()
        cutoff = today + relativedelta(days=days_ahead)

        return WarrantyRegistration.query.filter(
            WarrantyRegistration.status == WarrantyRegistration.STATUS_ACTIVE,
            WarrantyRegistration.warranty_end <= cutoff,
            WarrantyRegistration.warranty_end >= today,
        ).all()

    @staticmethod
    def expire_stale_warranties() -> int:
        """
        Bulk-update warranties that have passed their end date
        but still have 'active' status.

        Returns:
            Number of warranties expired.
        """
        today = date.today()
        stale = WarrantyRegistration.query.filter(
            WarrantyRegistration.status == WarrantyRegistration.STATUS_ACTIVE,
            WarrantyRegistration.warranty_end < today,
        ).all()

        count = 0
        for warranty in stale:
            warranty.status = WarrantyRegistration.STATUS_EXPIRED
            count += 1

        if count:
            db.session.commit()
        return count

    @staticmethod
    def get_warranty_stats(user_id: int) -> dict:
        """Get warranty statistics for a user."""
        total = WarrantyRegistration.query.filter_by(user_id=user_id).count()
        active = WarrantyRegistration.query.filter_by(
            user_id=user_id,
            status=WarrantyRegistration.STATUS_ACTIVE,
        ).count()
        expired = WarrantyRegistration.query.filter_by(
            user_id=user_id,
            status=WarrantyRegistration.STATUS_EXPIRED,
        ).count()
        claimed = WarrantyRegistration.query.filter_by(
            user_id=user_id,
            status=WarrantyRegistration.STATUS_CLAIMED,
        ).count()

        return {
            "total": total,
            "active": active,
            "expired": expired,
            "claimed": claimed,
        }
