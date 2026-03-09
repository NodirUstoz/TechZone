"""
Database Models Package

Import all models here so that Alembic and the app factory can discover them.
"""
from .user import User
from .product import Product, Category, Specification, Brand, ProductImage
from .order import Order, OrderItem, Payment
from .review import Review, TechReview
from .comparison import ComparisonList, comparison_products
from .price_alert import PriceAlert, PriceHistory
from .warranty import WarrantyRegistration

__all__ = [
    "User",
    "Product",
    "Category",
    "Specification",
    "Brand",
    "ProductImage",
    "Order",
    "OrderItem",
    "Payment",
    "Review",
    "TechReview",
    "ComparisonList",
    "comparison_products",
    "PriceAlert",
    "PriceHistory",
    "WarrantyRegistration",
]
