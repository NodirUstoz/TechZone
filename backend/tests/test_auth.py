"""
Tests for Authentication API Endpoints
"""
import json
import pytest


class TestRegister:
    """Tests for POST /api/auth/register"""

    def test_register_success(self, client):
        """Registering with valid data returns 201 and tokens."""
        payload = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "StrongPass1!",
            "first_name": "New",
            "last_name": "User",
        }
        response = client.post(
            "/api/auth/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "newuser@example.com"

    def test_register_duplicate_email(self, client, sample_user):
        """Registering with an existing email returns 409."""
        payload = {
            "email": sample_user.email,
            "username": "anotherusername",
            "password": "StrongPass1!",
            "first_name": "Dup",
            "last_name": "User",
        }
        response = client.post(
            "/api/auth/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 409
        assert "already registered" in response.get_json()["error"].lower()

    def test_register_duplicate_username(self, client, sample_user):
        """Registering with an existing username returns 409."""
        payload = {
            "email": "unique@example.com",
            "username": sample_user.username,
            "password": "StrongPass1!",
            "first_name": "Dup",
            "last_name": "User",
        }
        response = client.post(
            "/api/auth/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 409

    def test_register_weak_password(self, client):
        """Registering with a weak password returns 400."""
        payload = {
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "abc",
            "first_name": "Weak",
            "last_name": "Password",
        }
        response = client.post(
            "/api/auth/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_register_missing_fields(self, client):
        """Registering without required fields returns 400."""
        payload = {"email": "partial@example.com"}
        response = client.post(
            "/api/auth/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "details" in data


class TestLogin:
    """Tests for POST /api/auth/login"""

    def test_login_success(self, client, sample_user):
        """Logging in with correct credentials returns 200 and tokens."""
        payload = {
            "email": sample_user.email,
            "password": "TestPass1!",
        }
        response = client.post(
            "/api/auth/login",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["id"] == sample_user.id

    def test_login_wrong_password(self, client, sample_user):
        """Logging in with wrong password returns 401."""
        payload = {
            "email": sample_user.email,
            "password": "WrongPassword1!",
        }
        response = client.post(
            "/api/auth/login",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_login_nonexistent_email(self, client):
        """Logging in with unknown email returns 401."""
        payload = {
            "email": "nobody@example.com",
            "password": "AnyPassword1!",
        }
        response = client.post(
            "/api/auth/login",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_login_deactivated_account(self, client, db):
        """Logging in to a deactivated account returns 403."""
        from app.models.user import User

        user = User(
            email="inactive@test.com",
            username="inactiveuser",
            first_name="Inactive",
            last_name="User",
            is_active=False,
        )
        user.set_password("TestPass1!")
        db.session.add(user)
        db.session.commit()

        payload = {"email": "inactive@test.com", "password": "TestPass1!"}
        response = client.post(
            "/api/auth/login",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 403


class TestMe:
    """Tests for GET/PUT /api/auth/me"""

    def test_get_me_authenticated(self, client, auth_headers, sample_user):
        """Authenticated user can retrieve their profile."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["id"] == sample_user.id
        assert data["user"]["email"] == sample_user.email

    def test_get_me_unauthenticated(self, client):
        """Unauthenticated request to /me returns 401."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_update_profile(self, client, auth_headers):
        """User can update their profile fields."""
        payload = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone": "+15551234567",
        }
        response = client.put(
            "/api/auth/me",
            data=json.dumps(payload),
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["user"]["first_name"] == "Updated"

    def test_change_password(self, client, auth_headers):
        """User can change their password with correct current password."""
        payload = {
            "current_password": "TestPass1!",
            "new_password": "NewSecure2@",
        }
        response = client.put(
            "/api/auth/me",
            data=json.dumps(payload),
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_change_password_wrong_current(self, client, auth_headers):
        """Changing password with wrong current password returns 400."""
        payload = {
            "current_password": "WrongCurrent1!",
            "new_password": "NewSecure2@",
        }
        response = client.put(
            "/api/auth/me",
            data=json.dumps(payload),
            headers=auth_headers,
        )
        assert response.status_code == 400
