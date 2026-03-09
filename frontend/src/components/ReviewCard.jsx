/**
 * ReviewCard Component
 *
 * Displays a single user review with rating stars, pros/cons,
 * helpfulness voting, and verified purchase badge.
 */
import React, { useState } from "react";
import {
  FaStar,
  FaRegStar,
  FaStarHalfAlt,
  FaThumbsUp,
  FaThumbsDown,
  FaCheckCircle,
} from "react-icons/fa";

/**
 * Renders a row of star icons for a given rating (1-5).
 */
function StarRating({ rating }) {
  const stars = [];
  for (let i = 1; i <= 5; i++) {
    if (rating >= i) {
      stars.push(<FaStar key={i} className="review-card__star review-card__star--filled" />);
    } else if (rating >= i - 0.5) {
      stars.push(<FaStarHalfAlt key={i} className="review-card__star review-card__star--half" />);
    } else {
      stars.push(<FaRegStar key={i} className="review-card__star review-card__star--empty" />);
    }
  }
  return <div className="review-card__stars">{stars}</div>;
}

export default function ReviewCard({ review, onVote }) {
  const [voted, setVoted] = useState(null); // 'helpful' | 'not_helpful' | null

  const handleVote = (isHelpful) => {
    if (voted) return; // Already voted
    setVoted(isHelpful ? "helpful" : "not_helpful");
    if (onVote) {
      onVote(review.id, isHelpful);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return "";
    return new Date(isoString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <div className="review-card">
      {/* Header */}
      <div className="review-card__header">
        <div className="review-card__user">
          {review.user?.avatar_url ? (
            <img
              src={review.user.avatar_url}
              alt={review.user.username}
              className="review-card__avatar"
            />
          ) : (
            <div className="review-card__avatar-placeholder">
              {review.user?.username?.[0]?.toUpperCase() || "?"}
            </div>
          )}
          <div>
            <span className="review-card__username">
              {review.user?.username || "Anonymous"}
            </span>
            {review.is_verified_purchase && (
              <span className="review-card__verified">
                <FaCheckCircle /> Verified Purchase
              </span>
            )}
          </div>
        </div>

        <span className="review-card__date">{formatDate(review.created_at)}</span>
      </div>

      {/* Rating and title */}
      <div className="review-card__rating-row">
        <StarRating rating={review.rating} />
        {review.title && <h4 className="review-card__title">{review.title}</h4>}
      </div>

      {/* Body */}
      {review.body && <p className="review-card__body">{review.body}</p>}

      {/* Pros and cons */}
      {(review.pros?.length > 0 || review.cons?.length > 0) && (
        <div className="review-card__pros-cons">
          {review.pros?.length > 0 && (
            <div className="review-card__pros">
              <h5>Pros</h5>
              <ul>
                {review.pros.map((pro, idx) => (
                  <li key={idx}>+ {pro}</li>
                ))}
              </ul>
            </div>
          )}
          {review.cons?.length > 0 && (
            <div className="review-card__cons">
              <h5>Cons</h5>
              <ul>
                {review.cons.map((con, idx) => (
                  <li key={idx}>- {con}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Helpfulness voting */}
      <div className="review-card__helpfulness">
        <span className="review-card__helpful-label">Was this review helpful?</span>
        <button
          className={`review-card__vote-btn ${voted === "helpful" ? "review-card__vote-btn--active" : ""}`}
          onClick={() => handleVote(true)}
          disabled={voted !== null}
          aria-label="Helpful"
        >
          <FaThumbsUp /> {review.helpful_count + (voted === "helpful" ? 1 : 0)}
        </button>
        <button
          className={`review-card__vote-btn ${voted === "not_helpful" ? "review-card__vote-btn--active" : ""}`}
          onClick={() => handleVote(false)}
          disabled={voted !== null}
          aria-label="Not helpful"
        >
          <FaThumbsDown /> {review.not_helpful_count + (voted === "not_helpful" ? 1 : 0)}
        </button>
      </div>
    </div>
  );
}
