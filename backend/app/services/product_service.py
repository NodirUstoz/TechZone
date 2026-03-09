"""
Product Service
"""
import re
from typing import Optional

from ..extensions import db
from ..models.product import Product, Specification, ProductImage
from ..models.price_alert import PriceHistory


class ProductService:
    """Business logic for product management."""

    @staticmethod
    def create_product(data: dict) -> Product:
        """
        Create a new product with specifications and images.

        Args:
            data: Validated product data including optional 'specifications' and 'images'.

        Returns:
            The newly created Product.
        """
        slug = ProductService._generate_slug(data["name"])

        product = Product(
            name=data["name"],
            slug=slug,
            sku=data["sku"],
            description=data.get("description"),
            short_description=data.get("short_description"),
            price=data["price"],
            compare_at_price=data.get("compare_at_price"),
            cost_price=data.get("cost_price"),
            stock_quantity=data.get("stock_quantity", 0),
            low_stock_threshold=data.get("low_stock_threshold", 5),
            is_featured=data.get("is_featured", False),
            weight_kg=data.get("weight_kg"),
            length_cm=data.get("length_cm"),
            width_cm=data.get("width_cm"),
            height_cm=data.get("height_cm"),
            warranty_months=data.get("warranty_months", 12),
            meta_title=data.get("meta_title"),
            meta_description=data.get("meta_description"),
            category_id=data["category_id"],
            brand_id=data["brand_id"],
        )
        db.session.add(product)
        db.session.flush()  # get product.id

        # Add specifications
        for idx, spec_data in enumerate(data.get("specifications", [])):
            spec = Specification(
                product_id=product.id,
                group=spec_data.get("group"),
                key=spec_data["key"],
                value=spec_data["value"],
                sort_order=spec_data.get("sort_order", idx),
            )
            db.session.add(spec)

        # Add images
        for idx, img_data in enumerate(data.get("images", [])):
            image = ProductImage(
                product_id=product.id,
                url=img_data["url"],
                alt_text=img_data.get("alt_text"),
                is_primary=img_data.get("is_primary", idx == 0),
                sort_order=img_data.get("sort_order", idx),
            )
            db.session.add(image)

        # Record initial price
        PriceHistory.record_price(product.id, float(data["price"]), source="initial")

        db.session.commit()
        return product

    @staticmethod
    def update_product(product: Product, data: dict) -> Product:
        """
        Update an existing product.

        Args:
            product: The product to update.
            data: Dictionary of fields to update.

        Returns:
            The updated Product.
        """
        price_changed = False
        old_price = float(product.price)

        # Update scalar fields
        scalar_fields = [
            "name", "description", "short_description", "price",
            "compare_at_price", "cost_price", "stock_quantity",
            "low_stock_threshold", "is_featured", "is_active",
            "weight_kg", "length_cm", "width_cm", "height_cm",
            "warranty_months", "meta_title", "meta_description",
            "category_id", "brand_id",
        ]
        for field in scalar_fields:
            if field in data:
                setattr(product, field, data[field])
                if field == "price" and float(data["price"]) != old_price:
                    price_changed = True

        # Regenerate slug if name changed
        if "name" in data:
            product.slug = ProductService._generate_slug(data["name"], exclude_id=product.id)

        # Replace specifications if provided
        if "specifications" in data:
            Specification.query.filter_by(product_id=product.id).delete()
            for idx, spec_data in enumerate(data["specifications"]):
                spec = Specification(
                    product_id=product.id,
                    group=spec_data.get("group"),
                    key=spec_data["key"],
                    value=spec_data["value"],
                    sort_order=spec_data.get("sort_order", idx),
                )
                db.session.add(spec)

        # Replace images if provided
        if "images" in data:
            ProductImage.query.filter_by(product_id=product.id).delete()
            for idx, img_data in enumerate(data["images"]):
                image = ProductImage(
                    product_id=product.id,
                    url=img_data["url"],
                    alt_text=img_data.get("alt_text"),
                    is_primary=img_data.get("is_primary", idx == 0),
                    sort_order=img_data.get("sort_order", idx),
                )
                db.session.add(image)

        # Record price change
        if price_changed:
            PriceHistory.record_price(product.id, float(product.price), source="admin_update")

        db.session.commit()
        return product

    @staticmethod
    def _generate_slug(name: str, exclude_id: Optional[int] = None) -> str:
        """Generate a unique URL slug from a product name."""
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

        # Ensure uniqueness
        base_slug = slug
        counter = 1
        while True:
            query = Product.query.filter_by(slug=slug)
            if exclude_id:
                query = query.filter(Product.id != exclude_id)
            if not query.first():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    @staticmethod
    def reindex_all(elasticsearch_client) -> int:
        """Reindex all active products in Elasticsearch. Returns count."""
        products = Product.query.filter_by(is_active=True).all()
        for product in products:
            elasticsearch_client.index(
                index="products",
                id=product.id,
                document=product.to_search_dict(),
            )
        return len(products)
