"""
Review and TechReview Models
"""
from datetime import datetime, timezone

from ..extensions import db


class Review(db.Model):
    """User-submitted product review."""

    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(200), nullable=True)
    body = db.Column(db.Text, nullable=True)
    pros = db.Column(db.Text, nullable=True)  # stored as JSON string list
    cons = db.Column(db.Text, nullable=True)  # stored as JSON string list

    is_verified_purchase = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=True)

    # Helpfulness voting
    helpful_count = db.Column(db.Integer, default=0)
    not_helpful_count = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    product = db.relationship("Product", back_populates="reviews")
    user = db.relationship("User", back_populates="reviews")

    # One review per user per product
    __table_args__ = (
        db.UniqueConstraint("product_id", "user_id", name="uq_review_user_product"),
    )

    @property
    def helpfulness_score(self) -> float:
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0.0
        return round(self.helpful_count / total * 100, 1)

    def to_dict(self) -> dict:
        import json

        pros_list = []
        cons_list = []
        try:
            if self.pros:
                pros_list = json.loads(self.pros)
        except (json.JSONDecodeError, TypeError):
            pros_list = [self.pros] if self.pros else []
        try:
            if self.cons:
                cons_list = json.loads(self.cons)
        except (json.JSONDecodeError, TypeError):
            cons_list = [self.cons] if self.cons else []

        return {
            "id": self.id,
            "product_id": self.product_id,
            "user": {
                "id": self.user.id,
                "username": self.user.username,
                "avatar_url": self.user.avatar_url,
            } if self.user else None,
            "rating": self.rating,
            "title": self.title,
            "body": self.body,
            "pros": pros_list,
            "cons": cons_list,
            "is_verified_purchase": self.is_verified_purchase,
            "helpful_count": self.helpful_count,
            "not_helpful_count": self.not_helpful_count,
            "helpfulness_score": self.helpfulness_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Review {self.id} - {self.rating} stars>"


class TechReview(db.Model):
    """Professional editorial / tech review with multi-dimensional scoring."""

    __tablename__ = "tech_reviews"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), unique=True, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Headline and content
    title = db.Column(db.String(300), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    body = db.Column(db.Text, nullable=False)  # HTML or Markdown content
    verdict = db.Column(db.Text, nullable=False)

    # Multi-dimensional scores (1.0 - 10.0)
    score_performance = db.Column(db.Numeric(3, 1), nullable=False)
    score_value = db.Column(db.Numeric(3, 1), nullable=False)
    score_design = db.Column(db.Numeric(3, 1), nullable=False)
    score_features = db.Column(db.Numeric(3, 1), nullable=False)
    score_battery = db.Column(db.Numeric(3, 1), nullable=True)  # nullable for non-portable devices

    # Pros and cons stored as JSON string lists
    pros = db.Column(db.Text, nullable=True)
    cons = db.Column(db.Text, nullable=True)

    # Award badge (e.g., "Editor's Choice", "Best Value")
    award = db.Column(db.String(100), nullable=True)

    is_published = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    published_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    product = db.relationship("Product", back_populates="tech_review")
    author = db.relationship("User")

    @property
    def overall_score(self) -> float:
        """Calculate weighted overall score from dimensions."""
        scores = [
            float(self.score_performance),
            float(self.score_value),
            float(self.score_design),
            float(self.score_features),
        ]
        if self.score_battery is not None:
            scores.append(float(self.score_battery))
        return round(sum(scores) / len(scores), 1)

    def to_dict(self) -> dict:
        import json

        pros_list = []
        cons_list = []
        try:
            if self.pros:
                pros_list = json.loads(self.pros)
        except (json.JSONDecodeError, TypeError):
            pros_list = []
        try:
            if self.cons:
                cons_list = json.loads(self.cons)
        except (json.JSONDecodeError, TypeError):
            cons_list = []

        return {
            "id": self.id,
            "product_id": self.product_id,
            "author": {
                "id": self.author.id,
                "username": self.author.username,
                "full_name": self.author.full_name,
            } if self.author else None,
            "title": self.title,
            "summary": self.summary,
            "body": self.body,
            "verdict": self.verdict,
            "scores": {
                "performance": float(self.score_performance),
                "value": float(self.score_value),
                "design": float(self.score_design),
                "features": float(self.score_features),
                "battery": float(self.score_battery) if self.score_battery else None,
                "overall": self.overall_score,
            },
            "pros": pros_list,
            "cons": cons_list,
            "award": self.award,
            "is_published": self.is_published,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<TechReview '{self.title}' ({self.overall_score}/10)>"
