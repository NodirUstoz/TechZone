"""
ComparisonList Model
"""
from datetime import datetime, timezone

from ..extensions import db

# Association table for many-to-many: comparison <-> products
comparison_products = db.Table(
    "comparison_products",
    db.Column("comparison_id", db.Integer, db.ForeignKey("comparison_lists.id", ondelete="CASCADE"), primary_key=True),
    db.Column("product_id", db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    db.Column("added_at", db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
)

MAX_COMPARISON_PRODUCTS = 4


class ComparisonList(db.Model):
    """Saved product comparison list."""

    __tablename__ = "comparison_lists"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False, default="My Comparison")
    share_token = db.Column(db.String(36), unique=True, nullable=True)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = db.relationship("User", back_populates="comparison_lists")
    products = db.relationship("Product", secondary=comparison_products, lazy="joined",
                               backref=db.backref("comparison_lists", lazy="dynamic"))

    def add_product(self, product) -> None:
        """Add a product to the comparison, enforcing the max limit."""
        if product in self.products:
            raise ValueError("Product is already in this comparison list.")
        if len(self.products) >= MAX_COMPARISON_PRODUCTS:
            raise ValueError(f"Cannot compare more than {MAX_COMPARISON_PRODUCTS} products.")
        self.products.append(product)

    def remove_product(self, product) -> None:
        """Remove a product from the comparison."""
        if product not in self.products:
            raise ValueError("Product is not in this comparison list.")
        self.products.remove(product)

    def generate_share_token(self) -> str:
        import uuid
        self.share_token = str(uuid.uuid4())
        self.is_public = True
        return self.share_token

    def get_comparison_data(self) -> dict:
        """Build a structured comparison with aligned specification rows."""
        if not self.products:
            return {"products": [], "spec_groups": {}}

        # Collect all unique spec keys grouped by group name
        all_specs = {}
        for product in self.products:
            for spec in product.specifications:
                group = spec.group or "General"
                if group not in all_specs:
                    all_specs[group] = {}
                if spec.key not in all_specs[group]:
                    all_specs[group][spec.key] = {}
                all_specs[group][spec.key][product.id] = spec.value

        # Build aligned rows
        spec_groups = {}
        for group_name, keys in all_specs.items():
            rows = []
            for key, product_values in keys.items():
                row = {"key": key, "values": {}}
                values_set = set()
                for product in self.products:
                    val = product_values.get(product.id, "-")
                    row["values"][product.id] = val
                    values_set.add(val)
                row["is_different"] = len(values_set) > 1
                rows.append(row)
            spec_groups[group_name] = rows

        return {
            "products": [p.to_dict(include_specs=False) for p in self.products],
            "spec_groups": spec_groups,
        }

    def to_dict(self, include_comparison: bool = False) -> dict:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "share_token": self.share_token,
            "is_public": self.is_public,
            "product_count": len(self.products),
            "products": [p.to_dict(include_specs=False) for p in self.products],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_comparison:
            data["comparison"] = self.get_comparison_data()
        return data

    def __repr__(self) -> str:
        return f"<ComparisonList '{self.name}' ({len(self.products)} products)>"
