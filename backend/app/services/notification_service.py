"""
Notification Service
"""
from typing import Optional

from flask import current_app
from flask_mail import Message

from ..extensions import mail, db


class NotificationService:
    """Handles email and in-app notifications."""

    @staticmethod
    def send_email(
        recipient: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """
        Send an email notification.

        Args:
            recipient: Email address of the recipient.
            subject: Email subject line.
            html_body: HTML content of the email.
            text_body: Plain-text fallback.

        Returns:
            True if email was sent successfully, False otherwise.
        """
        try:
            msg = Message(
                subject=subject,
                recipients=[recipient],
                html=html_body,
                body=text_body or "",
                sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
            )
            mail.send(msg)
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to send email to {recipient}: {e}")
            return False

    @staticmethod
    def send_price_alert_email(user_email: str, product_name: str, current_price: float, target_price: float) -> bool:
        """Send a price drop notification email."""
        subject = f"Price Alert: {product_name} has dropped to ${current_price:.2f}!"
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1a1a2e; color: #fff; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">TechZone</h1>
                <p style="margin: 5px 0 0;">Price Alert Notification</p>
            </div>
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #16213e;">Great news! A product on your watchlist dropped in price.</h2>
                <div style="background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6;">
                    <h3 style="margin-top: 0;">{product_name}</h3>
                    <p style="font-size: 24px; color: #28a745; font-weight: bold;">
                        ${current_price:.2f}
                    </p>
                    <p style="color: #6c757d;">
                        Your target price: ${target_price:.2f}
                    </p>
                    <a href="#" style="display: inline-block; background: #0f3460; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin-top: 10px;">
                        View Product
                    </a>
                </div>
            </div>
            <div style="padding: 15px; text-align: center; color: #6c757d; font-size: 12px;">
                <p>You received this email because you set a price alert on TechZone.</p>
            </div>
        </div>
        """
        return NotificationService.send_email(user_email, subject, html_body)

    @staticmethod
    def send_order_confirmation_email(user_email: str, order_number: str, total: float, items_count: int) -> bool:
        """Send an order confirmation email."""
        subject = f"Order Confirmed: #{order_number}"
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1a1a2e; color: #fff; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">TechZone</h1>
                <p style="margin: 5px 0 0;">Order Confirmation</p>
            </div>
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #16213e;">Thank you for your order!</h2>
                <div style="background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6;">
                    <p><strong>Order Number:</strong> #{order_number}</p>
                    <p><strong>Items:</strong> {items_count}</p>
                    <p><strong>Total:</strong> ${total:.2f}</p>
                </div>
                <p style="margin-top: 20px; color: #6c757d;">
                    We will send you another email once your order has shipped.
                </p>
            </div>
            <div style="padding: 15px; text-align: center; color: #6c757d; font-size: 12px;">
                <p>TechZone - Your Electronics Destination</p>
            </div>
        </div>
        """
        return NotificationService.send_email(user_email, subject, html_body)

    @staticmethod
    def send_warranty_reminder_email(user_email: str, product_name: str, warranty_end: str, days_remaining: int) -> bool:
        """Send a warranty expiry reminder email."""
        subject = f"Warranty Reminder: {product_name} expires in {days_remaining} days"
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1a1a2e; color: #fff; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">TechZone</h1>
                <p style="margin: 5px 0 0;">Warranty Reminder</p>
            </div>
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #e63946;">Your warranty is expiring soon</h2>
                <div style="background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6;">
                    <h3 style="margin-top: 0;">{product_name}</h3>
                    <p><strong>Warranty Expires:</strong> {warranty_end}</p>
                    <p><strong>Days Remaining:</strong> {days_remaining}</p>
                    <p style="color: #6c757d;">
                        If you need to make a warranty claim, please do so before the expiration date.
                    </p>
                    <a href="#" style="display: inline-block; background: #0f3460; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin-top: 10px;">
                        View Warranty
                    </a>
                </div>
            </div>
            <div style="padding: 15px; text-align: center; color: #6c757d; font-size: 12px;">
                <p>TechZone - Your Electronics Destination</p>
            </div>
        </div>
        """
        return NotificationService.send_email(user_email, subject, html_body)

    @staticmethod
    def send_shipping_update_email(user_email: str, order_number: str, tracking_number: str, carrier: str) -> bool:
        """Send a shipping update email."""
        subject = f"Your Order #{order_number} Has Shipped!"
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1a1a2e; color: #fff; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">TechZone</h1>
                <p style="margin: 5px 0 0;">Shipping Update</p>
            </div>
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #16213e;">Your order is on its way!</h2>
                <div style="background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6;">
                    <p><strong>Order Number:</strong> #{order_number}</p>
                    <p><strong>Carrier:</strong> {carrier}</p>
                    <p><strong>Tracking Number:</strong> {tracking_number}</p>
                </div>
            </div>
            <div style="padding: 15px; text-align: center; color: #6c757d; font-size: 12px;">
                <p>TechZone - Your Electronics Destination</p>
            </div>
        </div>
        """
        return NotificationService.send_email(user_email, subject, html_body)
