"""
Product, Category, Specification, Brand, and ProductImage Models
"""
from datetime import datetime, timezone

from ..extensions import db


class Category(db.Model):
    """Product category with optional parent for hierarchy."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Self-referential relationship for subcategories
    parent = db.relationship("Category", remote_side=[id], backref=db.backref("children", lazy="dynamic"))
    products = db.relationship("Product", back_populates="category", lazy="dynamic")

    def to_dict(self, include_children: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "image_url": self.image_url,
            "parent_id": self.parent_id,
            "sort_order": self.sort_order,
            "product_count": self.products.count(),
        }
        if include_children:
            data["children"] = [child.to_dict() for child in self.children]
        return data

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


class Brand(db.Model):
    """Product brand / manufacturer."""

    __tablename__ = "brands"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    logo_url = db.Column(db.String(500), nullable=True)
    website_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    products = db.relationship("Product", back_populates="brand", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "logo_url": self.logo_url,
            "website_url": self.website_url,
            "product_count": self.products.count(),
        }

    def __repr__(self) -> str:
        return f"<Brand {self.name}>"


class Product(db.Model):
    """Electronics product."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    slug = db.Column(db.String(300), unique=True, nullable=False, index=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    short_description = db.Column(db.String(500), nullable=True)

    # Pricing
    price = db.Column(db.Numeric(10, 2), nullable=False)
    compare_at_price = db.Column(db.Numeric(10, 2), nullable=True)  # original / MSRP
    cost_price = db.Column(db.Numeric(10, 2), nullable=True)

    # Inventory
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    low_stock_threshold = db.Column(db.Integer, default=5)
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)

    # Dimensions and weight (for shipping)
    weight_kg = db.Column(db.Numeric(6, 2), nullable=True)
    length_cm = db.Column(db.Numeric(6, 2), nullable=True)
    width_cm = db.Column(db.Numeric(6, 2), nullable=True)
    height_cm = db.Column(db.Numeric(6, 2), nullable=True)

    # Warranty
    warranty_months = db.Column(db.Integer, default=12)

    # SEO
    meta_title = db.Column(db.String(255), nullable=True)
    meta_description = db.Column(db.String(500), nullable=True)

    # Foreign keys
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)
    brand_id = db.Column(db.Integer, db.ForeignKey("brands.id"), nullable=False, index=True)

    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    category = db.relationship("Category", back_populates="products")
    brand = db.relationship("Brand", back_populates="products")
    images = db.relationship("ProductImage", back_populates="product", lazy="joined", cascade="all, delete-orphan",
                             order_by="ProductImage.sort_order")
    specifications = db.relationship("Specification", back_populates="product", lazy="joined",
                                     cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="product", lazy="dynamic")
    tech_review = db.relationship("TechReview", back_populates="product", uselist=False)
    price_history = db.relationship("PriceHistory", back_populates="product", lazy="dynamic",
                                    order_by="PriceHistory.recorded_at.desc()")
    price_alerts = db.relationship("PriceAlert", back_populates="product", lazy="dynamic")

    @property
    def in_stock(self) -> bool:
        return self.stock_quantity > 0

    @property
    def low_stock(self) -> bool:
        return 0 < self.stock_quantity <= self.low_stock_threshold

    @property
    def primary_image_url(self) -> str | None:
        primary = next((img for img in self.images if img.is_primary), None)
        if primary:
            return primary.url
        return self.images[0].url if self.images else None

    @property
    def average_rating(self) -> float | None:
        ratings = [r.rating for r in self.reviews if r.is_approved]
        return round(sum(ratings) / len(ratings), 1) if ratings else None

    @property
    def review_count(self) -> int:
        return self.reviews.filter_by(is_approved=True).count()

    @property
    def discount_percentage(self) -> int | None:
        if self.compare_at_price and self.compare_at_price > self.price:
            return int(((self.compare_at_price - self.price) / self.compare_at_price) * 100)
        return None

    def to_dict(self, include_specs: bool = False, include_images: bool = True) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "sku": self.sku,
            "description": self.description,
            "short_description": self.short_description,
            "price": float(self.price),
            "compare_at_price": float(self.compare_at_price) if self.compare_at_price else None,
            "discount_percentage": self.discount_percentage,
            "stock_quantity": self.stock_quantity,
            "in_stock": self.in_stock,
            "low_stock": self.low_stock,
            "is_featured": self.is_featured,
            "warranty_months": self.warranty_months,
            "category": self.category.to_dict() if self.category else None,
            "brand": self.brand.to_dict() if self.brand else None,
            "primary_image_url": self.primary_image_url,
            "average_rating": self.average_rating,
            "review_count": self.review_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_images:
            data["images"] = [img.to_dict() for img in self.images]

        if include_specs:
            data["specifications"] = [spec.to_dict() for spec in self.specifications]

        return data

    def to_search_dict(self) -> dict:
        """Serialize for Elasticsearch indexing."""
        return {
            "name": self.name,
            "description": self.description or "",
            "brand": self.brand.name if self.brand else "",
            "category": self.category.name if self.category else "",
            "price": float(self.price),
            "specs": {s.key: s.value for s in self.specifications},
            "rating": self.average_rating or 0,
            "in_stock": self.in_stock,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Product {self.name}>"


class ProductImage(db.Model):
    """Product image with ordering support."""

    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    alt_text = db.Column(db.String(255), nullable=True)
    is_primary = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    product = db.relationship("Product", back_populates="images")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "alt_text": self.alt_text,
            "is_primary": self.is_primary,
            "sort_order": self.sort_order,
        }

    def __repr__(self) -> str:
        return f"<ProductImage {self.id} for product {self.product_id}>"


class Specification(db.Model):
    """Key-value product specification (e.g., CPU: Intel i7-13700K)."""

    __tablename__ = "specifications"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    group = db.Column(db.String(100), nullable=True)  # e.g. "Display", "Performance", "Connectivity"
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(500), nullable=False)
    sort_order = db.Column(db.Integer, default=0)

    product = db.relationship("Product", back_populates="specifications")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "group": self.group,
            "key": self.key,
            "value": self.value,
            "sort_order": self.sort_order,
        }

    def __repr__(self) -> str:
        return f"<Specification {self.key}={self.value}>"
