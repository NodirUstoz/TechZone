"""
Authentication Service
"""
from typing import Optional

from ..extensions import db
from ..models.user import User


class AuthService:
    """Handles user registration and authentication logic."""

    @staticmethod
    def register_user(
        email: str,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str = "customer",
    ) -> User:
        """
        Register a new user account.

        Args:
            email: User email address.
            username: Unique username.
            password: Plaintext password (will be hashed).
            first_name: First name.
            last_name: Last name.
            role: User role (default: customer).

        Returns:
            The newly created User instance.
        """
        user = User(
            email=email.lower().strip(),
            username=username.strip(),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            role=role,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return user

    @staticmethod
    def authenticate(email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.

        Returns:
            User if credentials are valid, None otherwise.
        """
        user = User.query.filter_by(email=email.lower().strip()).first()
        if user and user.check_password(password):
            return user
        return None

    @staticmethod
    def change_password(user: User, current_password: str, new_password: str) -> bool:
        """
        Change a user's password after verifying the current one.

        Returns:
            True if password was changed, False if current password is wrong.
        """
        if not user.check_password(current_password):
            return False

        user.set_password(new_password)
        db.session.commit()
        return True

    @staticmethod
    def deactivate_account(user: User) -> None:
        """Deactivate a user account."""
        user.is_active = False
        db.session.commit()

    @staticmethod
    def reactivate_account(user: User) -> None:
        """Reactivate a user account."""
        user.is_active = True
        db.session.commit()
