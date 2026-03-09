"""
Price Tracker Service
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from flask import current_app

from ..extensions import db
from ..models.product import Product
from ..models.price_alert import PriceAlert, PriceHistory


class PriceTracker:
    """
    Tracks product prices and triggers alerts when target prices are met.

    Used by Celery tasks to perform periodic price checks.
    """

    @staticmethod
    def record_current_prices() -> int:
        """
        Record the current price of all active products to the price history.

        Returns:
            Number of price records created.
        """
        products = Product.query.filter_by(is_active=True).all()
        count = 0

        for product in products:
            # Only record if the price differs from the last recorded price
            last_entry = (
                PriceHistory.query
                .filter_by(product_id=product.id)
                .order_by(PriceHistory.recorded_at.desc())
                .first()
            )

            if last_entry is None or float(last_entry.price) != float(product.price):
                PriceHistory.record_price(product.id, float(product.price), source="tracker")
                count += 1

        db.session.commit()
        return count

    @staticmethod
    def check_alerts() -> list[dict]:
        """
        Check all active price alerts and trigger those whose target has been met.

        Returns:
            List of triggered alert details (for notification dispatch).
        """
        triggered = []

        active_alerts = PriceAlert.query.filter_by(is_active=True, is_triggered=False).all()

        for alert in active_alerts:
            product = alert.product
            if not product or not product.is_active:
                continue

            if product.price <= alert.target_price:
                alert.trigger()
                triggered.append({
                    "alert_id": alert.id,
                    "user_id": alert.user_id,
                    "user_email": alert.user.email,
                    "product_id": product.id,
                    "product_name": product.name,
                    "target_price": float(alert.target_price),
                    "current_price": float(product.price),
                })

        db.session.commit()
        return triggered

    @staticmethod
    def update_product_price(product_id: int, new_price: float, source: str = "manual") -> Optional[Product]:
        """
        Update a product's price and record the change.

        Args:
            product_id: ID of the product to update.
            new_price: The new price.
            source: Source of the price update.

        Returns:
            The updated product, or None if not found.
        """
        product = Product.query.get(product_id)
        if not product:
            return None

        old_price = float(product.price)
        if old_price == new_price:
            return product

        product.price = Decimal(str(new_price))
        PriceHistory.record_price(product.id, new_price, source=source)

        db.session.commit()
        return product

    @staticmethod
    def get_price_stats(product_id: int, days: int = 90) -> dict:
        """
        Get price statistics for a product over a given period.

        Args:
            product_id: Product ID.
            days: Number of days to look back.

        Returns:
            Dictionary with min, max, average, current price, and trend.
        """
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        entries = (
            PriceHistory.query
            .filter(
                PriceHistory.product_id == product_id,
                PriceHistory.recorded_at >= cutoff,
            )
            .order_by(PriceHistory.recorded_at.asc())
            .all()
        )

        if not entries:
            product = Product.query.get(product_id)
            current = float(product.price) if product else 0
            return {
                "min": current,
                "max": current,
                "average": current,
                "current": current,
                "trend": "stable",
                "data_points": 0,
            }

        prices = [float(e.price) for e in entries]
        current = prices[-1]

        # Determine trend
        if len(prices) >= 2:
            recent_avg = sum(prices[-3:]) / min(len(prices), 3)
            older_avg = sum(prices[:3]) / min(len(prices), 3)
            if recent_avg < older_avg * 0.97:
                trend = "falling"
            elif recent_avg > older_avg * 1.03:
                trend = "rising"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "min": min(prices),
            "max": max(prices),
            "average": round(sum(prices) / len(prices), 2),
            "current": current,
            "trend": trend,
            "data_points": len(prices),
        }
