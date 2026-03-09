/**
 * ProductCard Component
 *
 * Displays a product summary card used in grid layouts.
 * Shows image, name, price, rating, and add-to-cart button.
 */
import React from "react";
import { Link } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { FaStar, FaShoppingCart, FaHeart } from "react-icons/fa";

import { addToCart, selectIsInCart } from "../store/slices/cartSlice";

export default function ProductCard({ product }) {
  const dispatch = useDispatch();
  const isInCart = useSelector(selectIsInCart(product.id));

  const handleAddToCart = (e) => {
    e.preventDefault();
    e.stopPropagation();
    dispatch(
      addToCart({
        id: product.id,
        name: product.name,
        price: product.price,
        image_url: product.primary_image_url,
        sku: product.sku,
        max_quantity: product.stock_quantity,
      })
    );
  };

  const discount = product.discount_percentage;
  const hasRating = product.average_rating !== null;

  return (
    <div className="product-card">
      <Link to={`/products/${product.id}`} className="product-card__link">
        {/* Image */}
        <div className="product-card__image-wrapper">
          {product.primary_image_url ? (
            <img
              src={product.primary_image_url}
              alt={product.name}
              className="product-card__image"
              loading="lazy"
            />
          ) : (
            <div className="product-card__image-placeholder">No Image</div>
          )}

          {discount && (
            <span className="product-card__badge product-card__badge--discount">
              -{discount}%
            </span>
          )}

          {product.is_featured && (
            <span className="product-card__badge product-card__badge--featured">
              Featured
            </span>
          )}

          {!product.in_stock && (
            <div className="product-card__overlay">Out of Stock</div>
          )}
        </div>

        {/* Info */}
        <div className="product-card__info">
          {product.brand && (
            <span className="product-card__brand">{product.brand.name}</span>
          )}

          <h3 className="product-card__name">{product.name}</h3>

          {/* Rating */}
          {hasRating && (
            <div className="product-card__rating">
              <FaStar className="product-card__star" />
              <span className="product-card__rating-value">
                {product.average_rating}
              </span>
              <span className="product-card__review-count">
                ({product.review_count})
              </span>
            </div>
          )}

          {/* Price */}
          <div className="product-card__price-row">
            <span className="product-card__price">
              ${product.price.toFixed(2)}
            </span>
            {product.compare_at_price && (
              <span className="product-card__compare-price">
                ${product.compare_at_price.toFixed(2)}
              </span>
            )}
          </div>
        </div>
      </Link>

      {/* Actions */}
      <div className="product-card__actions">
        <button
          className={`product-card__cart-btn ${isInCart ? "product-card__cart-btn--in-cart" : ""}`}
          onClick={handleAddToCart}
          disabled={!product.in_stock}
          title={isInCart ? "Already in cart" : "Add to cart"}
        >
          <FaShoppingCart />
          <span>{isInCart ? "In Cart" : "Add to Cart"}</span>
        </button>

        <button className="product-card__wishlist-btn" title="Add to wishlist">
          <FaHeart />
        </button>
      </div>
    </div>
  );
}
