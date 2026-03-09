"""
Product, Category, and Brand API Endpoints
"""
from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, current_user

from ..extensions import db
from ..models.product import Product, Category, Brand, Specification, ProductImage
from ..schemas.product_schema import ProductCreateSchema, ProductUpdateSchema
from ..utils.decorators import admin_required
from ..utils.pagination import paginate_query
from ..services.product_service import ProductService


class ProductListResource(Resource):
    """GET /api/products  |  POST /api/products"""

    def get(self):
        query = Product.query.filter_by(is_active=True)

        # Filters
        brand_id = request.args.get("brand_id", type=int)
        category_id = request.args.get("category_id", type=int)
        min_price = request.args.get("min_price", type=float)
        max_price = request.args.get("max_price", type=float)
        in_stock = request.args.get("in_stock", type=str)
        is_featured = request.args.get("is_featured", type=str)

        if brand_id:
            query = query.filter_by(brand_id=brand_id)
        if category_id:
            query = query.filter_by(category_id=category_id)
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        if in_stock and in_stock.lower() == "true":
            query = query.filter(Product.stock_quantity > 0)
        if is_featured and is_featured.lower() == "true":
            query = query.filter_by(is_featured=True)

        # Sorting
        sort = request.args.get("sort", "created_at")
        order = request.args.get("order", "desc")
        sort_map = {
            "price": Product.price,
            "name": Product.name,
            "created_at": Product.created_at,
        }
        sort_col = sort_map.get(sort, Product.created_at)
        if order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        return paginate_query(query, lambda p: p.to_dict())

    @jwt_required()
    @admin_required
    def post(self):
        schema = ProductCreateSchema()
        errors = schema.validate(request.json or {})
        if errors:
            return {"error": "Validation failed", "details": errors}, 400

        data = schema.load(request.json)
        product = ProductService.create_product(data)

        # Index in Elasticsearch
        if current_app.elasticsearch:
            try:
                current_app.elasticsearch.index(
                    index="products", id=product.id, document=product.to_search_dict()
                )
            except Exception:
                current_app.logger.warning("Failed to index product in Elasticsearch")

        return {"message": "Product created.", "product": product.to_dict(include_specs=True)}, 201


class ProductDetailResource(Resource):
    """GET/PUT/DELETE /api/products/<product_id>"""

    def get(self, product_id):
        product = Product.query.get_or_404(product_id)
        return {"product": product.to_dict(include_specs=True)}, 200

    @jwt_required()
    @admin_required
    def put(self, product_id):
        product = Product.query.get_or_404(product_id)
        schema = ProductUpdateSchema()
        errors = schema.validate(request.json or {})
        if errors:
            return {"error": "Validation failed", "details": errors}, 400

        data = schema.load(request.json)
        product = ProductService.update_product(product, data)

        # Re-index in Elasticsearch
        if current_app.elasticsearch:
            try:
                current_app.elasticsearch.index(
                    index="products", id=product.id, document=product.to_search_dict()
                )
            except Exception:
                current_app.logger.warning("Failed to re-index product in Elasticsearch")

        return {"message": "Product updated.", "product": product.to_dict(include_specs=True)}, 200

    @jwt_required()
    @admin_required
    def delete(self, product_id):
        product = Product.query.get_or_404(product_id)
        product.is_active = False
        db.session.commit()

        # Remove from Elasticsearch
        if current_app.elasticsearch:
            try:
                current_app.elasticsearch.delete(index="products", id=product_id, ignore=[404])
            except Exception:
                pass

        return {"message": "Product deleted."}, 200


class ProductSearchResource(Resource):
    """GET /api/products/search?q=..."""

    def get(self):
        query_text = request.args.get("q", "").strip()
        if not query_text:
            return {"error": "Search query 'q' is required."}, 400

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        # Try Elasticsearch first
        if current_app.elasticsearch:
            try:
                body = {
                    "query": {
                        "multi_match": {
                            "query": query_text,
                            "fields": ["name^3", "description", "brand^2", "category"],
                            "fuzziness": "AUTO",
                        }
                    },
                    "from": (page - 1) * per_page,
                    "size": per_page,
                }
                result = current_app.elasticsearch.search(index="products", body=body)
                hits = result["hits"]
                product_ids = [int(hit["_id"]) for hit in hits["hits"]]
                products = Product.query.filter(Product.id.in_(product_ids)).all()

                # Maintain ES ordering
                product_map = {p.id: p for p in products}
                ordered = [product_map[pid] for pid in product_ids if pid in product_map]

                return {
                    "products": [p.to_dict() for p in ordered],
                    "total": hits["total"]["value"],
                    "page": page,
                    "per_page": per_page,
                }, 200
            except Exception as e:
                current_app.logger.warning(f"Elasticsearch search failed, falling back to SQL: {e}")

        # Fallback: SQL ILIKE search
        sql_query = Product.query.filter(
            Product.is_active == True,
            db.or_(
                Product.name.ilike(f"%{query_text}%"),
                Product.description.ilike(f"%{query_text}%"),
            ),
        )
        return paginate_query(sql_query, lambda p: p.to_dict())


class CategoryListResource(Resource):
    """GET /api/categories"""

    def get(self):
        include_children = request.args.get("include_children", "false").lower() == "true"
        # Return only top-level categories
        categories = Category.query.filter_by(parent_id=None, is_active=True).order_by(Category.sort_order).all()
        return {
            "categories": [c.to_dict(include_children=include_children) for c in categories]
        }, 200


class CategoryProductsResource(Resource):
    """GET /api/categories/<category_id>/products"""

    def get(self, category_id):
        category = Category.query.get_or_404(category_id)
        query = Product.query.filter_by(category_id=category_id, is_active=True)

        sort = request.args.get("sort", "created_at")
        order = request.args.get("order", "desc")
        sort_map = {
            "price": Product.price,
            "name": Product.name,
            "created_at": Product.created_at,
        }
        sort_col = sort_map.get(sort, Product.created_at)
        query = query.order_by(sort_col.desc() if order == "desc" else sort_col.asc())

        result = paginate_query(query, lambda p: p.to_dict())
        result["category"] = category.to_dict()
        return result


class BrandListResource(Resource):
    """GET /api/brands"""

    def get(self):
        brands = Brand.query.filter_by(is_active=True).order_by(Brand.name).all()
        return {"brands": [b.to_dict() for b in brands]}, 200
