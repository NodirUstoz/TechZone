"""
API Blueprint Registration

All API resources are registered under the /api prefix.
"""
from flask import Blueprint
from flask_restful import Api

api_bp = Blueprint("api", __name__)
api = Api(api_bp)

# Import and register resources after Api creation to avoid circular imports
from .auth import RegisterResource, LoginResource, RefreshResource, MeResource
from .products import (
    ProductListResource, ProductDetailResource, ProductSearchResource,
    CategoryListResource, CategoryProductsResource, BrandListResource,
)
from .orders import OrderListResource, OrderDetailResource, OrderCancelResource
from .reviews import ProductReviewsResource, ReviewDetailResource, TechReviewResource
from .comparisons import ComparisonListResource, ComparisonDetailResource, ComparisonProductsResource
from .price_alerts import PriceAlertListResource, PriceAlertDetailResource, PriceHistoryResource
from .warranties import WarrantyListResource, WarrantyDetailResource, WarrantyClaimResource
from .admin import AdminDashboardResource, AdminUsersResource, AdminUserDetailResource, AdminOrdersResource, AdminOrderDetailResource

# ---- Auth ----
api.add_resource(RegisterResource, "/auth/register")
api.add_resource(LoginResource, "/auth/login")
api.add_resource(RefreshResource, "/auth/refresh")
api.add_resource(MeResource, "/auth/me")

# ---- Products ----
api.add_resource(ProductListResource, "/products")
api.add_resource(ProductDetailResource, "/products/<int:product_id>")
api.add_resource(ProductSearchResource, "/products/search")
api.add_resource(CategoryListResource, "/categories")
api.add_resource(CategoryProductsResource, "/categories/<int:category_id>/products")
api.add_resource(BrandListResource, "/brands")

# ---- Orders ----
api.add_resource(OrderListResource, "/orders")
api.add_resource(OrderDetailResource, "/orders/<int:order_id>")
api.add_resource(OrderCancelResource, "/orders/<int:order_id>/cancel")

# ---- Reviews ----
api.add_resource(ProductReviewsResource, "/products/<int:product_id>/reviews")
api.add_resource(ReviewDetailResource, "/reviews/<int:review_id>")
api.add_resource(TechReviewResource, "/products/<int:product_id>/tech-review")

# ---- Comparisons ----
api.add_resource(ComparisonListResource, "/comparisons")
api.add_resource(ComparisonDetailResource, "/comparisons/<int:comparison_id>")
api.add_resource(ComparisonProductsResource, "/comparisons/<int:comparison_id>/products")

# ---- Price Alerts ----
api.add_resource(PriceAlertListResource, "/price-alerts")
api.add_resource(PriceAlertDetailResource, "/price-alerts/<int:alert_id>")
api.add_resource(PriceHistoryResource, "/products/<int:product_id>/price-history")

# ---- Warranties ----
api.add_resource(WarrantyListResource, "/warranties")
api.add_resource(WarrantyDetailResource, "/warranties/<int:warranty_id>")
api.add_resource(WarrantyClaimResource, "/warranties/<int:warranty_id>/claim")

# ---- Admin ----
api.add_resource(AdminDashboardResource, "/admin/dashboard")
api.add_resource(AdminUsersResource, "/admin/users")
api.add_resource(AdminUserDetailResource, "/admin/users/<int:user_id>")
api.add_resource(AdminOrdersResource, "/admin/orders")
api.add_resource(AdminOrderDetailResource, "/admin/orders/<int:order_id>")
