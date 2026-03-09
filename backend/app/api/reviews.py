"""
Review and TechReview API Endpoints
"""
import json
from datetime import datetime, timezone

from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, current_user, get_jwt_identity
from marshmallow import Schema, fields, validate

from ..extensions import db
from ..models.review import Review, TechReview
from ..models.product import Product
from ..models.order import Order, OrderItem
from ..utils.decorators import admin_required
from ..utils.pagination import paginate_query


class ReviewCreateSchema(Schema):
    rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    title = fields.String(load_default=None, validate=validate.Length(max=200))
    body = fields.String(load_default=None)
    pros = fields.List(fields.String(), load_default=[])
    cons = fields.List(fields.String(), load_default=[])


class TechReviewSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=5, max=300))
    summary = fields.String(required=True)
    body = fields.String(required=True)
    verdict = fields.String(required=True)
    score_performance = fields.Float(required=True, validate=validate.Range(min=1.0, max=10.0))
    score_value = fields.Float(required=True, validate=validate.Range(min=1.0, max=10.0))
    score_design = fields.Float(required=True, validate=validate.Range(min=1.0, max=10.0))
    score_features = fields.Float(required=True, validate=validate.Range(min=1.0, max=10.0))
    score_battery = fields.Float(load_default=None, validate=validate.Range(min=1.0, max=10.0))
    pros = fields.List(fields.String(), load_default=[])
    cons = fields.List(fields.String(), load_default=[])
    award = fields.String(load_default=None, validate=validate.Length(max=100))
    is_published = fields.Boolean(load_default=False)


class ProductReviewsResource(Resource):
    """GET /api/products/<product_id>/reviews  |  POST"""

    def get(self, product_id):
        Product.query.get_or_404(product_id)
        query = Review.query.filter_by(product_id=product_id, is_approved=True)

        # Sorting
        sort = request.args.get("sort", "created_at")
        if sort == "helpful":
            query = query.order_by(Review.helpful_count.desc())
        elif sort == "rating_high":
            query = query.order_by(Review.rating.desc())
        elif sort == "rating_low":
            query = query.order_by(Review.rating.asc())
        else:
            query = query.order_by(Review.created_at.desc())

        result = paginate_query(query, lambda r: r.to_dict())

        # Add rating distribution
        all_reviews = Review.query.filter_by(product_id=product_id, is_approved=True).all()
        distribution = {i: 0 for i in range(1, 6)}
        for r in all_reviews:
            distribution[r.rating] = distribution.get(r.rating, 0) + 1

        result["rating_distribution"] = distribution
        result["total_reviews"] = len(all_reviews)
        result["average_rating"] = (
            round(sum(r.rating for r in all_reviews) / len(all_reviews), 1) if all_reviews else 0
        )

        return result

    @jwt_required()
    def post(self, product_id):
        product = Product.query.get_or_404(product_id)

        # Check if user already reviewed
        existing = Review.query.filter_by(product_id=product_id, user_id=current_user.id).first()
        if existing:
            return {"error": "You have already reviewed this product."}, 409

        schema = ReviewCreateSchema()
        errors = schema.validate(request.json or {})
        if errors:
            return {"error": "Validation failed", "details": errors}, 400

        data = schema.load(request.json)

        # Check for verified purchase
        is_verified = db.session.query(OrderItem).join(Order).filter(
            Order.user_id == current_user.id,
            Order.status.in_(["delivered", "shipped"]),
            OrderItem.product_id == product_id,
        ).first() is not None

        review = Review(
            product_id=product_id,
            user_id=current_user.id,
            rating=data["rating"],
            title=data.get("title"),
            body=data.get("body"),
            pros=json.dumps(data.get("pros", [])),
            cons=json.dumps(data.get("cons", [])),
            is_verified_purchase=is_verified,
        )

        db.session.add(review)
        db.session.commit()

        return {"message": "Review submitted.", "review": review.to_dict()}, 201


class ReviewDetailResource(Resource):
    """PUT/DELETE /api/reviews/<review_id>"""

    @jwt_required()
    def put(self, review_id):
        review = Review.query.get_or_404(review_id)
        if review.user_id != current_user.id:
            return {"error": "Not authorized."}, 403

        schema = ReviewCreateSchema()
        errors = schema.validate(request.json or {})
        if errors:
            return {"error": "Validation failed", "details": errors}, 400

        data = schema.load(request.json)
        review.rating = data["rating"]
        review.title = data.get("title")
        review.body = data.get("body")
        review.pros = json.dumps(data.get("pros", []))
        review.cons = json.dumps(data.get("cons", []))

        db.session.commit()
        return {"message": "Review updated.", "review": review.to_dict()}, 200

    @jwt_required()
    def delete(self, review_id):
        review = Review.query.get_or_404(review_id)
        if review.user_id != current_user.id and not current_user.is_admin:
            return {"error": "Not authorized."}, 403

        db.session.delete(review)
        db.session.commit()
        return {"message": "Review deleted."}, 200


class TechReviewResource(Resource):
    """GET /api/products/<product_id>/tech-review  |  POST"""

    def get(self, product_id):
        Product.query.get_or_404(product_id)
        tech_review = TechReview.query.filter_by(product_id=product_id, is_published=True).first()
        if not tech_review:
            return {"error": "No tech review found for this product."}, 404
        return {"tech_review": tech_review.to_dict()}, 200

    @jwt_required()
    @admin_required
    def post(self, product_id):
        product = Product.query.get_or_404(product_id)

        existing = TechReview.query.filter_by(product_id=product_id).first()
        if existing:
            return {"error": "A tech review already exists for this product. Use PUT to update."}, 409

        schema = TechReviewSchema()
        errors = schema.validate(request.json or {})
        if errors:
            return {"error": "Validation failed", "details": errors}, 400

        data = schema.load(request.json)

        tech_review = TechReview(
            product_id=product_id,
            author_id=current_user.id,
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

        return {"message": "Tech review created.", "tech_review": tech_review.to_dict()}, 201
