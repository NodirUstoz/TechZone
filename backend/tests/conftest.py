"""
Pytest Fixtures for TechZone Test Suite

Provides a test Flask app, database, authenticated client, and factory
helpers for creating test users, products, orders, etc.
"""
import pytest
from decimal import Decimal

from app import create_app
from app.extensions import db as _db
from app.models.user import User
from app.models.product import Product, Category, Brand, Specification, ProductImage
from app.models.order import Order, OrderItem, Payment


@pytest.fixture(scope="session")
def app():
    """Create the Flask application configured for testing."""
    app = create_app("testing")
    yield app


@pytest.fixture(scope="function")
def db(app):
    """
    Provide a clean database for each test function.

    Creates all tables before the test, drops them after.
    """
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture
def client(app, db):
    """Provide a Flask test client."""
    return app.test_client()


@pytest.fixture
def sample_user(db):
    """Create and return a sample customer user."""
    user = User(
        email="customer@test.com",
        username="testcustomer",
        first_name="Test",
        last_name="Customer",
        role="customer",
        is_active=True,
        email_verified=True,
    )
    user.set_password("TestPass1!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(db):
    """Create and return a sample admin user."""
    user = User(
        email="admin@test.com",
        username="testadmin",
        first_name="Test",
        last_name="Admin",
        role="admin",
        is_active=True,
        email_verified=True,
    )
    user.set_password("AdminPass1!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_category(db):
    """Create and return a sample product category."""
    category = Category(
        name="Laptops",
        slug="laptops",
        description="Portable computers",
        is_active=True,
    )
    db.session.add(category)
    db.session.commit()
    return category


@pytest.fixture
def sample_brand(db):
    """Create and return a sample brand."""
    brand = Brand(
        name="TestBrand",
        slug="testbrand",
        description="Test electronics brand",
        is_active=True,
    )
    db.session.add(brand)
    db.session.commit()
    return brand


@pytest.fixture
def sample_product(db, sample_category, sample_brand):
    """Create and return a sample product with specs and an image."""
    product = Product(
        name="Test Laptop Pro 15",
        slug="test-laptop-pro-15",
        sku="TLP-15-001",
        description="A powerful test laptop for development.",
        short_description="Pro-grade test laptop",
        price=Decimal("1299.99"),
        compare_at_price=Decimal("1499.99"),
        stock_quantity=25,
        low_stock_threshold=5,
        is_active=True,
        is_featured=True,
        weight_kg=Decimal("1.80"),
        warranty_months=24,
        category_id=sample_category.id,
        brand_id=sample_brand.id,
    )
    db.session.add(product)
    db.session.flush()

    # Add specifications
    specs = [
        Specification(product_id=product.id, group="Performance", key="CPU", value="Intel Core i7-13700H", sort_order=0),
        Specification(product_id=product.id, group="Performance", key="RAM", value="16GB DDR5", sort_order=1),
        Specification(product_id=product.id, group="Display", key="Screen Size", value="15.6 inches", sort_order=2),
        Specification(product_id=product.id, group="Display", key="Resolution", value="2560x1440", sort_order=3),
    ]
    for spec in specs:
        db.session.add(spec)

    # Add image
    image = ProductImage(
        product_id=product.id,
        url="https://cdn.example.com/products/test-laptop.jpg",
        alt_text="Test Laptop Pro 15",
        is_primary=True,
        sort_order=0,
    )
    db.session.add(image)
    db.session.commit()
    return product


@pytest.fixture
def auth_headers(app, sample_user):
    """Generate JWT authorization headers for the sample customer user."""
    from flask_jwt_extended import create_access_token

    with app.app_context():
        token = create_access_token(identity=sample_user.id)
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture
def admin_headers(app, admin_user):
    """Generate JWT authorization headers for the admin user."""
    from flask_jwt_extended import create_access_token

    with app.app_context():
        token = create_access_token(identity=admin_user.id)
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture
def sample_order(db, sample_user, sample_product):
    """Create and return a sample order with one item."""
    order = Order(
        user_id=sample_user.id,
        status=Order.STATUS_PAID,
        subtotal=sample_product.price,
        tax_amount=Decimal("104.00"),
        shipping_amount=Decimal("0.00"),
        total=sample_product.price + Decimal("104.00"),
        shipping_first_name=sample_user.first_name,
        shipping_last_name=sample_user.last_name,
        shipping_address_line1="123 Test St",
        shipping_city="Testville",
        shipping_state="TS",
        shipping_zip_code="12345",
        shipping_country="US",
    )
    db.session.add(order)
    db.session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=sample_product.id,
        quantity=1,
        unit_price=sample_product.price,
        product_name=sample_product.name,
        product_sku=sample_product.sku,
    )
    db.session.add(item)

    payment = Payment(
        order_id=order.id,
        amount=order.total,
        currency="USD",
        status=Payment.STATUS_COMPLETED,
        payment_method="card",
    )
    db.session.add(payment)
    db.session.commit()
    return order
