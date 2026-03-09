"""
Tests for Product API Endpoints
"""
import json
import pytest
from decimal import Decimal


class TestProductList:
    """Tests for GET /api/products"""

    def test_list_products(self, client, sample_product):
        """Listing products returns paginated results."""
        response = client.get("/api/products")
        assert response.status_code == 200
        data = response.get_json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert len(data["items"]) >= 1

    def test_list_products_filter_by_category(self, client, sample_product, sample_category):
        """Products can be filtered by category ID."""
        response = client.get(f"/api/products?category_id={sample_category.id}")
        assert response.status_code == 200
        data = response.get_json()
        for item in data["items"]:
            assert item["category"]["id"] == sample_category.id

    def test_list_products_filter_by_brand(self, client, sample_product, sample_brand):
        """Products can be filtered by brand ID."""
        response = client.get(f"/api/products?brand_id={sample_brand.id}")
        assert response.status_code == 200
        data = response.get_json()
        for item in data["items"]:
            assert item["brand"]["id"] == sample_brand.id

    def test_list_products_price_range(self, client, sample_product):
        """Products can be filtered by price range."""
        response = client.get("/api/products?min_price=1000&max_price=1500")
        assert response.status_code == 200
        data = response.get_json()
        for item in data["items"]:
            assert 1000 <= item["price"] <= 1500

    def test_list_products_in_stock_filter(self, client, sample_product):
        """Products can be filtered to show only in-stock items."""
        response = client.get("/api/products?in_stock=true")
        assert response.status_code == 200
        data = response.get_json()
        for item in data["items"]:
            assert item["in_stock"] is True

    def test_list_products_sort_by_price_asc(self, client, db, sample_category, sample_brand):
        """Products can be sorted by price ascending."""
        from app.models.product import Product

        p1 = Product(name="Cheap Item", slug="cheap-item", sku="CI-001", price=Decimal("99.99"),
                      stock_quantity=10, category_id=sample_category.id, brand_id=sample_brand.id)
        p2 = Product(name="Expensive Item", slug="expensive-item", sku="EI-001", price=Decimal("9999.99"),
                      stock_quantity=10, category_id=sample_category.id, brand_id=sample_brand.id)
        db.session.add_all([p1, p2])
        db.session.commit()

        response = client.get("/api/products?sort=price&order=asc")
        assert response.status_code == 200
        data = response.get_json()
        prices = [item["price"] for item in data["items"]]
        assert prices == sorted(prices)

    def test_list_products_pagination(self, client, sample_product):
        """Pagination parameters are respected."""
        response = client.get("/api/products?page=1&per_page=1")
        assert response.status_code == 200
        data = response.get_json()
        assert data["per_page"] == 1
        assert len(data["items"]) <= 1


class TestProductDetail:
    """Tests for GET /api/products/<product_id>"""

    def test_get_product(self, client, sample_product):
        """Fetching a product by ID returns full details with specs."""
        response = client.get(f"/api/products/{sample_product.id}")
        assert response.status_code == 200
        data = response.get_json()
        product = data["product"]
        assert product["id"] == sample_product.id
        assert product["name"] == "Test Laptop Pro 15"
        assert product["sku"] == "TLP-15-001"
        assert "specifications" in product
        assert len(product["specifications"]) == 4
        assert "images" in product
        assert product["in_stock"] is True
        assert product["discount_percentage"] is not None

    def test_get_product_not_found(self, client):
        """Fetching a non-existent product returns 404."""
        response = client.get("/api/products/999999")
        assert response.status_code == 404


class TestProductCreate:
    """Tests for POST /api/products (admin only)"""

    def test_create_product_as_admin(self, client, admin_headers, sample_category, sample_brand):
        """Admin can create a product with specs and images."""
        payload = {
            "name": "New Gaming Laptop",
            "sku": "NGL-001",
            "description": "High-performance gaming laptop",
            "price": 2499.99,
            "stock_quantity": 15,
            "category_id": sample_category.id,
            "brand_id": sample_brand.id,
            "specifications": [
                {"group": "Performance", "key": "GPU", "value": "NVIDIA RTX 4090"},
                {"group": "Performance", "key": "CPU", "value": "Intel i9-13900HX"},
            ],
            "images": [
                {"url": "https://cdn.example.com/gaming-laptop.jpg", "is_primary": True},
            ],
        }
        response = client.post(
            "/api/products",
            data=json.dumps(payload),
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["product"]["name"] == "New Gaming Laptop"
        assert len(data["product"]["specifications"]) == 2

    def test_create_product_as_customer_forbidden(self, client, auth_headers, sample_category, sample_brand):
        """Non-admin users cannot create products."""
        payload = {
            "name": "Unauthorized Product",
            "sku": "UNA-001",
            "price": 100.00,
            "category_id": sample_category.id,
            "brand_id": sample_brand.id,
        }
        response = client.post(
            "/api/products",
            data=json.dumps(payload),
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_create_product_missing_required_fields(self, client, admin_headers):
        """Creating a product without required fields returns 400."""
        payload = {"name": "Incomplete Product"}
        response = client.post(
            "/api/products",
            data=json.dumps(payload),
            headers=admin_headers,
        )
        assert response.status_code == 400


class TestCategories:
    """Tests for GET /api/categories"""

    def test_list_categories(self, client, sample_category):
        """Listing categories returns active top-level categories."""
        response = client.get("/api/categories")
        assert response.status_code == 200
        data = response.get_json()
        assert "categories" in data
        assert len(data["categories"]) >= 1
        assert data["categories"][0]["name"] == "Laptops"


class TestBrands:
    """Tests for GET /api/brands"""

    def test_list_brands(self, client, sample_brand):
        """Listing brands returns all active brands."""
        response = client.get("/api/brands")
        assert response.status_code == 200
        data = response.get_json()
        assert "brands" in data
        assert len(data["brands"]) >= 1
