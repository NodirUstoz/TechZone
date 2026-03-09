"""
Price-related Celery Tasks
"""
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def record_prices(self):
    """
    Record current prices for all active products.
    Scheduled to run periodically by Celery Beat.
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from app.services.price_tracker import PriceTracker
            count = PriceTracker.record_current_prices()
            logger.info(f"Recorded {count} price changes.")
            return {"recorded": count}
    except Exception as exc:
        logger.error(f"Price recording failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_price_alerts(self):
    """
    Check all active price alerts and trigger notifications for those
    whose target price has been met.
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from app.services.price_tracker import PriceTracker
            from app.tasks.notification_tasks import send_price_alert_notification

            triggered = PriceTracker.check_alerts()
            logger.info(f"Triggered {len(triggered)} price alerts.")

            # Dispatch notification for each triggered alert
            for alert_info in triggered:
                send_price_alert_notification.delay(
                    user_email=alert_info["user_email"],
                    product_name=alert_info["product_name"],
                    current_price=alert_info["current_price"],
                    target_price=alert_info["target_price"],
                    alert_id=alert_info["alert_id"],
                )

            return {"triggered": len(triggered)}
    except Exception as exc:
        logger.error(f"Price alert check failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2)
def update_product_price(self, product_id: int, new_price: float, source: str = "external"):
    """
    Update a product's price from an external source and check alerts.
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from app.services.price_tracker import PriceTracker
            product = PriceTracker.update_product_price(product_id, new_price, source=source)
            if product:
                logger.info(f"Updated price for product {product_id} to {new_price}")
                # Immediately check alerts for this product
                check_price_alerts.delay()
                return {"product_id": product_id, "new_price": new_price}
            else:
                logger.warning(f"Product {product_id} not found for price update.")
                return {"error": "Product not found"}
    except Exception as exc:
        logger.error(f"Product price update failed: {exc}")
        raise self.retry(exc=exc)
