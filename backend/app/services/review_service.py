"""
Review Service
"""
import json
from typing import Optional

from sqlalchemy import func

from ..extensions import db
from ..models.review import Review, TechReview
from ..models.order import Order, OrderItem
from ..models.product import Product


class ReviewService:
    """Business logic for product reviews and tech reviews."""

    @staticmethod
    def create_review(
        user_id: int,
        product_id: int,
        rating: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        pros: Optional[list] = None,
        cons: Optional[list] = None,
    ) -> Review:
        """
        Create a new product review.

        Automatically checks whether the user has purchased the product
        to set the verified_purchase flag.

        Args:
            user_id: ID of the reviewing user.
            product_id: ID of the product being reviewed.
            rating: Star rating (1-5).
            title: Optional review title.
            body: Optional review body text.
            pros: Optional list of pros.
            cons: Optional list of cons.

        Returns:
            The created Review instance.

        Raises:
            ValueError: If the user has already reviewed this product.
        """
        existing = Review.query.filter_by(user_id=user_id, product_id=product_id).first()
        if existing:
            raise ValueError("You have already reviewed this product.")

        # Check for verified purchase
        is_verified = db.session.query(
            db.exists().where(
                db.and_(
                    Order.user_id == user_id,
                    Order.status.in_(["paid", "processing", "shipped", "delivered"]),
                    OrderItem.order_id == Order.id,
                    OrderItem.product_id == product_id,
                )
            )
        ).scalar()

        review = Review(
            user_id=user_id,
            product_id=product_id,
            rating=rating,
            title=title,
            body=body,
            pros=json.dumps(pros) if pros else None,
            cons=json.dumps(cons) if cons else None,
            is_verified_purchase=is_verified,
        )
        db.session.add(review)
        db.session.commit()
        return review

    @staticmethod
    def update_review(review: Review, data: dict) -> Review:
        """
        Update an existing review.

        Args:
            review: The review to update.
            data: Dictionary of fields to update.

        Returns:
            The updated Review.
        """
        if "rating" in data:
            review.rating = data["rating"]
        if "title" in data:
            review.title = data["title"]
        if "body" in data:
            review.body = data["body"]
        if "pros" in data:
            review.pros = json.dumps(data["pros"]) if data["pros"] else None
        if "cons" in data:
            review.cons = json.dumps(data["cons"]) if data["cons"] else None

        db.session.commit()
        return review

    @staticmethod
    def vote_helpful(review_id: int, is_helpful: bool) -> Review:
        """
        Record a helpfulness vote on a review.

        Args:
            review_id: ID of the review.
            is_helpful: True for helpful, False for not helpful.

        Returns:
            The updated Review.

        Raises:
            ValueError: If the review is not found.
        """
        review = Review.query.get(review_id)
        if not review:
            raise ValueError("Review not found.")

        if is_helpful:
            review.helpful_count += 1
        else:
            review.not_helpful_count += 1

        db.session.commit()
        return review

    @staticmethod
    def get_product_rating_summary(product_id: int) -> dict:
        """
        Get a rating distribution summary for a product.

        Returns a dict with star counts, average rating, and total reviews.
        """
        results = (
            db.session.query(
                Review.rating,
                func.count(Review.id),
            )
            .filter(
                Review.product_id == product_id,
                Review.is_approved == True,
            )
            .group_by(Review.rating)
            .all()
        )

        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total_reviews = 0
        total_score = 0

        for rating, count in results:
            distribution[rating] = count
            total_reviews += count
            total_score += rating * count

        average = round(total_score / total_reviews, 1) if total_reviews > 0 else 0

        return {
            "average_rating": average,
            "total_reviews": total_reviews,
            "distribution": distribution,
        }

    @staticmethod
    def create_tech_review(
        product_id: int,
        author_id: int,
        data: dict,
    ) -> TechReview:
        """
        Create a professional tech review for a product.

        Args:
            product_id: ID of the product.
            author_id: ID of the admin author.
            data: Validated tech review data.

        Returns:
            The created TechReview.

        Raises:
            ValueError: If a tech review already exists for this product.
        """
        existing = TechReview.query.filter_by(product_id=product_id).first()
        if existing:
            raise ValueError("A tech review already exists for this product.")

        from datetime import datetime, timezone

        tech_review = TechReview(
            product_id=product_id,
            author_id=author_id,
            title=data["title"],
            summary=data["summary"],
            body=data["body"],
            verdict=data["verdict"],
            score_performance=data["score_performance"],
            score_value=data["score_value"],
            score_design=data["score_design"],
            score_features=data["score_features"],
            score_battery=data.get("score_battery"),
            pros=json.dumps(data.get("pros", [])),
            cons=json.dumps(data.get("cons", [])),
            award=data.get("award"),
            is_published=data.get("is_published", False),
        )

        if tech_review.is_published:
            tech_review.published_at = datetime.now(timezone.utc)

        db.session.add(tech_review)
        db.session.commit()
        return tech_review

    @staticmethod
    def moderate_review(review_id: int, approved: bool) -> Review:
        """
        Approve or reject a user review (admin action).

        Args:
            review_id: ID of the review.
            approved: Whether to approve the review.

        Returns:
            The updated Review.
        """
        review = Review.query.get(review_id)
        if not review:
            raise ValueError("Review not found.")

        review.is_approved = approved
        db.session.commit()
        return review
