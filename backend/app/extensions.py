"""
Flask Extension Instances

Extensions are instantiated here and initialized with the app in the factory.
This avoids circular imports.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()
ma = Marshmallow()


# ----------------------------------------------------------------
# JWT callbacks
# ----------------------------------------------------------------

@jwt.user_identity_loader
def user_identity_lookup(user_id):
    """Return the user id as the JWT identity."""
    return user_id


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Load user from database on each request that requires auth."""
    from .models.user import User
    identity = jwt_data["sub"]
    return User.query.get(identity)


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_data):
    return {"error": "Token expired", "message": "The access token has expired."}, 401


@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    return {"error": "Invalid token", "message": error_string}, 401


@jwt.unauthorized_loader
def missing_token_callback(error_string):
    return {"error": "Missing token", "message": "Authorization token is required."}, 401


@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_data):
    return {"error": "Revoked token", "message": "The token has been revoked."}, 401
