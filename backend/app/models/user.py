"""
User and AdminUser Models
"""
from datetime import datetime, timezone

import bcrypt

from ..extensions import db


class User(db.Model):
    """Application user model supporting customers and admins."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)

    # Address fields
    address_line1 = db.Column(db.String(255), nullable=True)
    address_line2 = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), nullable=True, default="US")

    # Role and status
    role = db.Column(db.String(20), nullable=False, default="customer")  # customer, admin
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    orders = db.relationship("Order", back_populates="user", lazy="dynamic")
    reviews = db.relationship("Review", back_populates="user", lazy="dynamic")
    price_alerts = db.relationship("PriceAlert", back_populates="user", lazy="dynamic")
    warranties = db.relationship("WarrantyRegistration", back_populates="user", lazy="dynamic")
    comparison_lists = db.relationship("ComparisonList", back_populates="user", lazy="dynamic")

    def set_password(self, password: str) -> None:
        """Hash and store the password."""
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def record_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login = datetime.now(timezone.utc)
        db.session.commit()

    def to_dict(self, include_private: bool = False) -> dict:
        """Serialize user to dictionary."""
        data = {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_private:
            data.update({
                "email": self.email,
                "phone": self.phone,
                "address_line1": self.address_line1,
                "address_line2": self.address_line2,
                "city": self.city,
                "state": self.state,
                "zip_code": self.zip_code,
                "country": self.country,
                "is_active": self.is_active,
                "email_verified": self.email_verified,
                "last_login": self.last_login.isoformat() if self.last_login else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            })

        return data

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"


class AdminUser:
    """
    Utility wrapper providing admin-specific helper methods.
    Not a separate DB table -- wraps a User with role='admin'.
    """

    def __init__(self, user: User):
        if user.role != "admin":
            raise ValueError("User is not an admin.")
        self._user = user

    @property
    def user(self) -> User:
        return self._user

    @staticmethod
    def get_all_admins():
        """Return all admin users."""
        return User.query.filter_by(role="admin", is_active=True).all()

    @staticmethod
    def promote_user(user: User) -> None:
        """Promote a regular user to admin."""
        user.role = "admin"
        db.session.commit()

    @staticmethod
    def demote_user(user: User) -> None:
        """Demote an admin to regular customer."""
        user.role = "customer"
        db.session.commit()
