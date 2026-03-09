"""
Generic Email Celery Tasks
"""
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_generic_email(self, recipient: str, subject: str, html_body: str, text_body: str = ""):
    """
    Send a generic email. Used as a catch-all for ad-hoc emails.

    Args:
        recipient: Email address.
        subject: Email subject line.
        html_body: HTML email content.
        text_body: Plain-text fallback.
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from app.services.notification_service import NotificationService
            success = NotificationService.send_email(
                recipient=recipient,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )
            logger.info(f"Generic email to {recipient}: {'sent' if success else 'failed'}")
            return {"sent": success, "recipient": recipient}
    except Exception as exc:
        logger.error(f"Generic email task failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, user_email: str, username: str):
    """
    Send a welcome email to a newly registered user.
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from app.services.notification_service import NotificationService

            subject = "Welcome to TechZone!"
            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #1a1a2e; color: #fff; padding: 20px; text-align: center;">
                    <h1 style="margin: 0;">TechZone</h1>
                </div>
                <div style="padding: 30px; background: #f8f9fa;">
                    <h2 style="color: #16213e;">Welcome, {username}!</h2>
                    <p>Thank you for joining TechZone, your one-stop shop for all things electronics.</p>
                    <div style="background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6;">
                        <h3>Here's what you can do:</h3>
                        <ul style="line-height: 2;">
                            <li>Browse thousands of electronics products</li>
                            <li>Compare products side-by-side</li>
                            <li>Set price alerts to never miss a deal</li>
                            <li>Read expert tech reviews</li>
                            <li>Manage your product warranties</li>
                        </ul>
                    </div>
                    <a href="#" style="display: inline-block; background: #0f3460; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin-top: 20px;">
                        Start Shopping
                    </a>
                </div>
                <div style="padding: 15px; text-align: center; color: #6c757d; font-size: 12px;">
                    <p>TechZone - Your Electronics Destination</p>
                </div>
            </div>
            """

            success = NotificationService.send_email(user_email, subject, html_body)
            logger.info(f"Welcome email to {user_email}: {'sent' if success else 'failed'}")
            return {"sent": success}
    except Exception as exc:
        logger.error(f"Welcome email task failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def send_bulk_promotional_email(self, subject: str, html_body: str, recipient_emails: list):
    """
    Send a promotional email to a list of recipients.
    Processes in batches to avoid overwhelming the SMTP server.
    """
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from app.services.notification_service import NotificationService
            import time

            success_count = 0
            fail_count = 0
            batch_size = 50

            for i in range(0, len(recipient_emails), batch_size):
                batch = recipient_emails[i:i + batch_size]
                for email in batch:
                    result = NotificationService.send_email(email, subject, html_body)
                    if result:
                        success_count += 1
                    else:
                        fail_count += 1

                # Small delay between batches
                if i + batch_size < len(recipient_emails):
                    time.sleep(2)

            logger.info(f"Bulk email: {success_count} sent, {fail_count} failed out of {len(recipient_emails)}")
            return {
                "total": len(recipient_emails),
                "sent": success_count,
                "failed": fail_count,
            }
    except Exception as exc:
        logger.error(f"Bulk email task failed: {exc}")
        raise self.retry(exc=exc)
