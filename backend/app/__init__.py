"""
TechZone Flask Application Factory
"""
from flask import Flask
from flask_cors import CORS

from .config import config_by_name
from .extensions import db, migrate, jwt, mail, ma


def create_app(config_name: str = "development") -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    _register_extensions(app)

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    # Register CLI commands
    _register_cli_commands(app)

    return app


def _register_extensions(app: Flask) -> None:
    """Register Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    ma.init_app(app)

    # Initialize Redis connection
    import redis
    app.redis = redis.from_url(app.config.get("REDIS_URL", "redis://localhost:6379/0"))

    # Initialize Elasticsearch
    if app.config.get("ELASTICSEARCH_URL"):
        from elasticsearch import Elasticsearch
        app.elasticsearch = Elasticsearch(app.config["ELASTICSEARCH_URL"])
    else:
        app.elasticsearch = None


def _register_blueprints(app: Flask) -> None:
    """Register API blueprints."""
    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")


def _register_error_handlers(app: Flask) -> None:
    """Register custom error handlers."""
    from flask import jsonify

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request", "message": str(error)}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"error": "Unauthorized", "message": "Authentication required."}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"error": "Forbidden", "message": "You do not have permission to access this resource."}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found", "message": "The requested resource was not found."}), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({"error": "Unprocessable entity", "message": str(error)}), 422

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"error": "Internal server error", "message": "An unexpected error occurred."}), 500


def _register_cli_commands(app: Flask) -> None:
    """Register custom Flask CLI commands."""
    import click

    @app.cli.command("seed")
    def seed_database():
        """Seed the database with initial data."""
        from .models.user import User
        from .models.product import Category, Brand

        click.echo("Seeding database...")

        # Create admin user
        admin = User.query.filter_by(email="admin@techzone.com").first()
        if not admin:
            admin = User(
                email="admin@techzone.com",
                username="admin",
                first_name="Admin",
                last_name="User",
                role="admin",
            )
            admin.set_password("Admin123!")
            db.session.add(admin)
            click.echo("  Created admin user (admin@techzone.com / Admin123!)")

        # Create categories
        categories_data = [
            {"name": "Laptops", "slug": "laptops", "description": "Portable computers for work and play"},
            {"name": "Smartphones", "slug": "smartphones", "description": "Mobile phones with advanced features"},
            {"name": "Tablets", "slug": "tablets", "description": "Touchscreen tablet devices"},
            {"name": "Monitors", "slug": "monitors", "description": "Display screens for computers"},
            {"name": "Headphones", "slug": "headphones", "description": "Audio headphones and earbuds"},
            {"name": "Cameras", "slug": "cameras", "description": "Digital cameras and accessories"},
            {"name": "Gaming", "slug": "gaming", "description": "Gaming consoles and accessories"},
            {"name": "Components", "slug": "components", "description": "PC components and parts"},
            {"name": "Storage", "slug": "storage", "description": "SSDs, HDDs, and external storage"},
            {"name": "Networking", "slug": "networking", "description": "Routers, switches, and networking gear"},
        ]

        for cat_data in categories_data:
            existing = Category.query.filter_by(slug=cat_data["slug"]).first()
            if not existing:
                cat = Category(**cat_data)
                db.session.add(cat)
                click.echo(f"  Created category: {cat_data['name']}")

        # Create brands
        brands_data = [
            {"name": "Apple", "slug": "apple", "description": "Consumer electronics and software"},
            {"name": "Samsung", "slug": "samsung", "description": "Electronics and technology conglomerate"},
            {"name": "Sony", "slug": "sony", "description": "Electronics, gaming, and entertainment"},
            {"name": "Dell", "slug": "dell", "description": "Computers and enterprise solutions"},
            {"name": "ASUS", "slug": "asus", "description": "Computers, phones, and components"},
            {"name": "Lenovo", "slug": "lenovo", "description": "PCs, tablets, and smart devices"},
            {"name": "HP", "slug": "hp", "description": "Computers, printers, and enterprise"},
            {"name": "LG", "slug": "lg", "description": "Electronics and home appliances"},
            {"name": "Bose", "slug": "bose", "description": "Audio equipment and speakers"},
            {"name": "NVIDIA", "slug": "nvidia", "description": "GPUs and AI computing"},
        ]

        for brand_data in brands_data:
            existing = Brand.query.filter_by(slug=brand_data["slug"]).first()
            if not existing:
                brand = Brand(**brand_data)
                db.session.add(brand)
                click.echo(f"  Created brand: {brand_data['name']}")

        db.session.commit()
        click.echo("Database seeded successfully.")

    @app.cli.command("create-index")
    def create_search_index():
        """Create Elasticsearch product index."""
        if not app.elasticsearch:
            click.echo("Elasticsearch is not configured.")
            return

        index_body = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "product_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "asciifolding", "edge_ngram_filter"],
                        }
                    },
                    "filter": {
                        "edge_ngram_filter": {
                            "type": "edge_ngram",
                            "min_gram": 2,
                            "max_gram": 20,
                        }
                    },
                },
            },
            "mappings": {
                "properties": {
                    "name": {"type": "text", "analyzer": "product_analyzer"},
                    "description": {"type": "text", "analyzer": "standard"},
                    "brand": {"type": "keyword"},
                    "category": {"type": "keyword"},
                    "price": {"type": "float"},
                    "specs": {"type": "object", "enabled": False},
                    "rating": {"type": "float"},
                    "in_stock": {"type": "boolean"},
                    "created_at": {"type": "date"},
                }
            },
        }

        if app.elasticsearch.indices.exists(index="products"):
            app.elasticsearch.indices.delete(index="products")
            click.echo("Deleted existing products index.")

        app.elasticsearch.indices.create(index="products", body=index_body)
        click.echo("Created products index in Elasticsearch.")
