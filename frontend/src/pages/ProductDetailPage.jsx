/**
 * ProductDetailPage
 *
 * Full product detail view with image gallery, specifications,
 * pricing, add-to-cart, reviews, and price history chart.
 */
import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import {
  FaStar,
  FaShoppingCart,
  FaExchangeAlt,
  FaBell,
  FaShieldAlt,
  FaCheckCircle,
  FaSpinner,
  FaChevronLeft,
  FaChevronRight,
} from "react-icons/fa";

import {
  fetchProductDetail,
  clearProductDetail,
  selectCurrentProduct,
  selectDetailLoading,
} from "../store/slices/productSlice";
import { addToCart, selectIsInCart } from "../store/slices/cartSlice";
import ReviewCard from "../components/ReviewCard";
import productApi from "../api/productApi";

export default function ProductDetailPage() {
  const { productId } = useParams();
  const dispatch = useDispatch();

  const product = useSelector(selectCurrentProduct);
  const loading = useSelector(selectDetailLoading);
  const isInCart = useSelector(selectIsInCart(parseInt(productId)));

  const [selectedImage, setSelectedImage] = useState(0);
  const [activeTab, setActiveTab] = useState("specs");
  const [reviews, setReviews] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(false);

  useEffect(() => {
    dispatch(fetchProductDetail(parseInt(productId)));
    return () => dispatch(clearProductDetail());
  }, [dispatch, productId]);

  // Load reviews when tab is opened
  useEffect(() => {
    if (activeTab === "reviews" && reviews.length === 0) {
      setReviewsLoading(true);
      productApi
        .getProductReviews(parseInt(productId))
        .then((data) => {
          setReviews(data.items || []);
        })
        .catch(() => {})
        .finally(() => setReviewsLoading(false));
    }
  }, [activeTab, productId, reviews.length]);

  const handleAddToCart = () => {
    if (!product) return;
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

  const navigateImage = (direction) => {
    if (!product?.images) return;
    const total = product.images.length;
    setSelectedImage((prev) => (prev + direction + total) % total);
  };

  if (loading) {
    return (
      <div className="product-detail__loading">
        <FaSpinner className="spinner" /> Loading product...
      </div>
    );
  }

  if (!product) {
    return (
      <div className="product-detail__not-found">
        <h2>Product Not Found</h2>
        <Link to="/products">Back to Products</Link>
      </div>
    );
  }

  const images = product.images || [];
  const currentImage = images[selectedImage];

  return (
    <div className="product-detail">
      {/* Breadcrumb */}
      <nav className="product-detail__breadcrumb">
        <Link to="/">Home</Link> / <Link to="/products">Products</Link> /{" "}
        {product.category && (
          <>
            <Link to={`/products?category_id=${product.category.id}`}>
              {product.category.name}
            </Link>{" "}
            /{" "}
          </>
        )}
        <span>{product.name}</span>
      </nav>

      <div className="product-detail__main">
        {/* Image gallery */}
        <div className="product-detail__gallery">
          <div className="product-detail__image-container">
            {images.length > 1 && (
              <button className="product-detail__nav-btn product-detail__nav-btn--prev" onClick={() => navigateImage(-1)}>
                <FaChevronLeft />
              </button>
            )}
            {currentImage ? (
              <img
                src={currentImage.url}
                alt={currentImage.alt_text || product.name}
                className="product-detail__main-image"
              />
            ) : (
              <div className="product-detail__no-image">No Image Available</div>
            )}
            {images.length > 1 && (
              <button className="product-detail__nav-btn product-detail__nav-btn--next" onClick={() => navigateImage(1)}>
                <FaChevronRight />
              </button>
            )}
          </div>

          {images.length > 1 && (
            <div className="product-detail__thumbnails">
              {images.map((img, idx) => (
                <button
                  key={img.id}
                  className={`product-detail__thumb ${idx === selectedImage ? "product-detail__thumb--active" : ""}`}
                  onClick={() => setSelectedImage(idx)}
                >
                  <img src={img.url} alt={img.alt_text || `View ${idx + 1}`} />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Product info */}
        <div className="product-detail__info">
          {product.brand && (
            <Link to={`/products?brand_id=${product.brand.id}`} className="product-detail__brand">
              {product.brand.name}
            </Link>
          )}

          <h1 className="product-detail__name">{product.name}</h1>

          {/* Rating */}
          {product.average_rating && (
            <div className="product-detail__rating">
              <FaStar className="product-detail__star" />
              <span>{product.average_rating}</span>
              <span className="product-detail__review-count">
                ({product.review_count} reviews)
              </span>
            </div>
          )}

          <p className="product-detail__sku">SKU: {product.sku}</p>

          {/* Price */}
          <div className="product-detail__price-section">
            <span className="product-detail__price">${product.price.toFixed(2)}</span>
            {product.compare_at_price && (
              <span className="product-detail__compare-price">
                ${product.compare_at_price.toFixed(2)}
              </span>
            )}
            {product.discount_percentage && (
              <span className="product-detail__discount-badge">
                Save {product.discount_percentage}%
              </span>
            )}
          </div>

          {/* Stock status */}
          <div className="product-detail__stock">
            {product.in_stock ? (
              <span className="product-detail__in-stock">
                <FaCheckCircle /> In Stock ({product.stock_quantity} available)
              </span>
            ) : (
              <span className="product-detail__out-of-stock">Out of Stock</span>
            )}
          </div>

          {/* Short description */}
          {product.short_description && (
            <p className="product-detail__short-desc">{product.short_description}</p>
          )}

          {/* Actions */}
          <div className="product-detail__actions">
            <button
              className={`product-detail__add-to-cart ${isInCart ? "product-detail__add-to-cart--in-cart" : ""}`}
              onClick={handleAddToCart}
              disabled={!product.in_stock}
            >
              <FaShoppingCart />
              {isInCart ? "Added to Cart" : "Add to Cart"}
            </button>

            <button className="product-detail__action-btn" title="Compare">
              <FaExchangeAlt /> Compare
            </button>
            <button className="product-detail__action-btn" title="Price alert">
              <FaBell /> Price Alert
            </button>
          </div>

          {/* Warranty info */}
          {product.warranty_months > 0 && (
            <div className="product-detail__warranty">
              <FaShieldAlt />
              <span>{product.warranty_months}-month warranty included</span>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="product-detail__tabs">
        <div className="product-detail__tab-nav">
          {["specs", "description", "reviews"].map((tab) => (
            <button
              key={tab}
              className={`product-detail__tab-btn ${activeTab === tab ? "product-detail__tab-btn--active" : ""}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab === "specs" && "Specifications"}
              {tab === "description" && "Description"}
              {tab === "reviews" && `Reviews (${product.review_count || 0})`}
            </button>
          ))}
        </div>

        <div className="product-detail__tab-content">
          {activeTab === "specs" && product.specifications && (
            <table className="product-detail__spec-table">
              <tbody>
                {product.specifications.map((spec) => (
                  <tr key={spec.id}>
                    <td className="product-detail__spec-group">{spec.group || "General"}</td>
                    <td className="product-detail__spec-key">{spec.key}</td>
                    <td className="product-detail__spec-value">{spec.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeTab === "description" && (
            <div className="product-detail__description">
              {product.description || "No description available."}
            </div>
          )}

          {activeTab === "reviews" && (
            <div className="product-detail__reviews">
              {reviewsLoading ? (
                <p><FaSpinner className="spinner" /> Loading reviews...</p>
              ) : reviews.length === 0 ? (
                <p>No reviews yet. Be the first to review this product!</p>
              ) : (
                reviews.map((review) => (
                  <ReviewCard key={review.id} review={review} />
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
