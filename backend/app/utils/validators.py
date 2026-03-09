"""
Custom Validators
"""
import re
from marshmallow import ValidationError


def validate_password(password: str) -> None:
    """
    Validate password strength.

    Rules:
    - At least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character

    Raises:
        ValidationError: If password does not meet requirements.
    """
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least one special character.")

    if errors:
        raise ValidationError(errors)


def validate_phone(phone: str) -> None:
    """
    Validate a phone number format.

    Accepts formats like:
    - +1-555-123-4567
    - (555) 123-4567
    - 5551234567
    - +44 20 7946 0958

    Raises:
        ValidationError: If phone format is invalid.
    """
    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone)
    if not re.match(r"^\+?\d{7,15}$", cleaned):
        raise ValidationError("Invalid phone number format.")


def validate_sku(sku: str) -> None:
    """
    Validate a product SKU.

    Rules:
    - 3-50 characters
    - Only alphanumeric, dashes, and underscores

    Raises:
        ValidationError: If SKU format is invalid.
    """
    if not re.match(r"^[A-Za-z0-9\-_]{3,50}$", sku):
        raise ValidationError(
            "SKU must be 3-50 characters and contain only letters, numbers, dashes, and underscores."
        )


def validate_slug(slug: str) -> None:
    """
    Validate a URL slug.

    Rules:
    - Lowercase alphanumeric and dashes only
    - No leading or trailing dashes
    - No consecutive dashes

    Raises:
        ValidationError: If slug format is invalid.
    """
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", slug):
        raise ValidationError(
            "Slug must contain only lowercase letters, numbers, and single dashes (no leading/trailing dashes)."
        )


def validate_rating(value: int) -> None:
    """Validate that a rating is between 1 and 5."""
    if not isinstance(value, int) or value < 1 or value > 5:
        raise ValidationError("Rating must be an integer between 1 and 5.")


def validate_price(value: float) -> None:
    """Validate that a price is positive."""
    if value is not None and value < 0:
        raise ValidationError("Price must be a positive number.")


def validate_quantity(value: int) -> None:
    """Validate that a quantity is at least 1."""
    if not isinstance(value, int) or value < 1:
        raise ValidationError("Quantity must be at least 1.")
