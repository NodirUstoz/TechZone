"""
Notification Celery Tasks
"""
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_price_alert_notification(self, user_email: str, product_name: str, current_price: float, target_price: float, alert_id: int):
    """
    Send a price alert email notification and mark the alert as notified.
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from app.services.notification_service import NotificationService
            from app.models.price_alert import PriceAlert
            from app.extensions import db

            success = NotificationService.send_price_alert_email(
                user_email=user_email,
                product_name=product_name,
                current_price=current_price,
                target_price=target_price,
            )

            if success:
                alert = PriceAlert.query.get(alert_id)
                if alert:
                    alert.mark_notified()
                    db.session.commit()
                logger.info(f"Price alert notification sent to {user_email} for {product_name}")
            else:
                logger.warning(f"Failed to send price alert email to {user_email}")

            return {"sent": success}
    except Exception as exc:
        logger.error(f"Price alert notification failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_order_confirmation(self, user_email: str, order_number: str, total: float, items_count: int):
    """Send order confirmation email."""
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from app.services.notification_service import NotificationService

            success = NotificationService.send_order_confirmation_email(
                user_email=user_email,
                order_number=order_number,
                total=total,
                items_count=items_count,
            )
            logger.info(f"Order confirmation {'sent' if success else 'failed'} for {order_number}")
            return {"sent": success}
    except Exception as exc:
        logger.error(f"Order confirmation email failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_shipping_notification(self, user_email: str, order_number: str, tracking_number: str, carrier: str):
    """Send shipping update email."""
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from app.services.notification_service import NotificationService

            success = NotificationService.send_shipping_update_email(
                user_email=user_email,
                order_number=order_number,
                tracking_number=tracking_number,
                carrier=carrier,
            )
            logger.info(f"Shipping notification {'sent' if success else 'failed'} for {order_number}")
            return {"sent": success}
    except Exception as exc:
        logger.error(f"Shipping notification failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2)
def check_warranty_expiry_reminders(self):
    """
    Check for warranties expiring within the reminder window
    and send reminder emails.
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from datetime import datetime, timedelta, timezone
            from app.models.warranty import WarrantyRegistration
            from app.services.notification_service import NotificationService
            from app.extensions import db

            reminder_days = app.config.get("WARRANTY_REMINDER_DAYS", 30)
            cutoff_date = (datetime.now(timezone.utc) + timedelta(days=reminder_days)).date()
            today = datetime.now(timezone.utc).date()

            warranties = WarrantyRegistration.query.filter(
                WarrantyRegistration.status == WarrantyRegistration.STATUS_ACTIVE,
                WarrantyRegistration.warranty_end <= cutoff_date,
                WarrantyRegistration.warranty_end > today,
                WarrantyRegistration.reminder_sent == False,
            ).all()

            sent_count = 0
            for warranty in warranties:
                success = NotificationService.send_warranty_reminder_email(
                    user_email=warranty.user.email,
                    product_name=warranty.product.name,
                    warranty_end=warranty.warranty_end.isoformat(),
                    days_remaining=warranty.days_remaining,
                )
                if success:
                    warranty.reminder_sent = True
                    warranty.reminder_sent_at = datetime.now(timezone.utc)
                    sent_count += 1

            db.session.commit()
            logger.info(f"Sent {sent_count} warranty expiry reminders.")
            return {"reminders_sent": sent_count}
    except Exception as exc:
        logger.error(f"Warranty expiry check failed: {exc}")
        raise self.retry(exc=exc)
