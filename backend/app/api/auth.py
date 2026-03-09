"""
Authentication API Endpoints
"""
from flask import request
from flask_restful import Resource
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, current_user,
)

from ..extensions import db
from ..models.user import User
from ..schemas.user_schema import UserRegisterSchema, UserLoginSchema, UserUpdateSchema
from ..services.auth_service import AuthService


class RegisterResource(Resource):
    """POST /api/auth/register"""

    def post(self):
        schema = UserRegisterSchema()
        errors = schema.validate(request.json or {})
        if errors:
            return {"error": "Validation failed", "details": errors}, 400

        data = schema.load(request.json)

        # Check for existing email or username
        if User.query.filter_by(email=data["email"]).first():
            return {"error": "Email already registered."}, 409
        if User.query.filter_by(username=data["username"]).first():
            return {"error": "Username already taken."}, 409

        user = AuthService.register_user(
            email=data["email"],
            username=data["username"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return {
            "message": "Registration successful.",
            "user": user.to_dict(include_private=True),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }, 201


class LoginResource(Resource):
    """POST /api/auth/login"""

    def post(self):
        schema = UserLoginSchema()
        errors = schema.validate(request.json or {})
        if errors:
            return {"error": "Validation failed", "details": errors}, 400

        data = schema.load(request.json)
        user = AuthService.authenticate(data["email"], data["password"])

        if not user:
            return {"error": "Invalid email or password."}, 401

        if not user.is_active:
            return {"error": "Account is deactivated. Contact support."}, 403

        user.record_login()

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return {
            "message": "Login successful.",
            "user": user.to_dict(include_private=True),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }, 200


class RefreshResource(Resource):
    """POST /api/auth/refresh"""

    @jwt_required(refresh=True)
    def post(self):
        identity = get_jwt_identity()
        access_token = create_access_token(identity=identity)
        return {"access_token": access_token}, 200


class MeResource(Resource):
    """GET/PUT /api/auth/me"""

    @jwt_required()
    def get(self):
        return {"user": current_user.to_dict(include_private=True)}, 200

    @jwt_required()
    def put(self):
        schema = UserUpdateSchema()
        errors = schema.validate(request.json or {})
        if errors:
            return {"error": "Validation failed", "details": errors}, 400

        data = schema.load(request.json)

        # Check username uniqueness if changing
        if "username" in data and data["username"] != current_user.username:
            existing = User.query.filter_by(username=data["username"]).first()
            if existing:
                return {"error": "Username already taken."}, 409

        # Update fields
        updatable = [
            "username", "first_name", "last_name", "phone",
            "address_line1", "address_line2", "city", "state",
            "zip_code", "country",
        ]
        for field in updatable:
            if field in data:
                setattr(current_user, field, data[field])

        # Handle password change
        if "new_password" in data:
            if "current_password" not in data:
                return {"error": "Current password is required to set a new password."}, 400
            if not current_user.check_password(data["current_password"]):
                return {"error": "Current password is incorrect."}, 400
            current_user.set_password(data["new_password"])

        db.session.commit()

        return {
            "message": "Profile updated.",
            "user": current_user.to_dict(include_private=True),
        }, 200
