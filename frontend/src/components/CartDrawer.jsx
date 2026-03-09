/**
 * CartDrawer Component
 *
 * A slide-in cart panel displaying current cart items, quantities,
 * subtotals, and a checkout button.
 */
import React from "react";
import { Link } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { FaTimes, FaPlus, FaMinus, FaTrash, FaShoppingBag } from "react-icons/fa";

import {
  selectCartItems,
  selectCartSubtotal,
  selectCartShipping,
  selectCartTax,
  selectCartTotal,
  selectCartItemCount,
  incrementQuantity,
  decrementQuantity,
  removeFromCart,
  clearCart,
} from "../store/slices/cartSlice";

export default function CartDrawer({ isOpen, onClose }) {
  const dispatch = useDispatch();

  const items = useSelector(selectCartItems);
  const subtotal = useSelector(selectCartSubtotal);
  const shipping = useSelector(selectCartShipping);
  const tax = useSelector(selectCartTax);
  const total = useSelector(selectCartTotal);
  const itemCount = useSelector(selectCartItemCount);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="cart-drawer__backdrop" onClick={onClose} />

      {/* Drawer */}
      <aside className="cart-drawer" role="dialog" aria-label="Shopping cart">
        {/* Header */}
        <div className="cart-drawer__header">
          <h2 className="cart-drawer__title">
            <FaShoppingBag /> Cart ({itemCount})
          </h2>
          <button className="cart-drawer__close" onClick={onClose} aria-label="Close cart">
            <FaTimes />
          </button>
        </div>

        {/* Items */}
        {items.length === 0 ? (
          <div className="cart-drawer__empty">
            <p>Your cart is empty.</p>
            <Link to="/products" className="cart-drawer__browse-btn" onClick={onClose}>
              Browse Products
            </Link>
          </div>
        ) : (
          <>
            <ul className="cart-drawer__items">
              {items.map((item) => (
                <li key={item.id} className="cart-drawer__item">
                  <div className="cart-drawer__item-image">
                    {item.image_url ? (
                      <img src={item.image_url} alt={item.name} />
                    ) : (
                      <div className="cart-drawer__item-placeholder" />
                    )}
                  </div>

                  <div className="cart-drawer__item-details">
                    <Link
                      to={`/products/${item.id}`}
                      className="cart-drawer__item-name"
                      onClick={onClose}
                    >
                      {item.name}
                    </Link>
                    <span className="cart-drawer__item-sku">{item.sku}</span>
                    <span className="cart-drawer__item-price">
                      ${item.price.toFixed(2)}
                    </span>
                  </div>

                  <div className="cart-drawer__item-controls">
                    <div className="cart-drawer__qty">
                      <button
                        onClick={() => dispatch(decrementQuantity(item.id))}
                        aria-label="Decrease quantity"
                        className="cart-drawer__qty-btn"
                      >
                        <FaMinus />
                      </button>
                      <span className="cart-drawer__qty-value">{item.quantity}</span>
                      <button
                        onClick={() => dispatch(incrementQuantity(item.id))}
                        aria-label="Increase quantity"
                        className="cart-drawer__qty-btn"
                        disabled={item.quantity >= item.max_quantity}
                      >
                        <FaPlus />
                      </button>
                    </div>

                    <span className="cart-drawer__item-total">
                      ${(item.price * item.quantity).toFixed(2)}
                    </span>

                    <button
                      className="cart-drawer__remove-btn"
                      onClick={() => dispatch(removeFromCart(item.id))}
                      aria-label={`Remove ${item.name}`}
                    >
                      <FaTrash />
                    </button>
                  </div>
                </li>
              ))}
            </ul>

            {/* Summary */}
            <div className="cart-drawer__summary">
              <div className="cart-drawer__summary-row">
                <span>Subtotal</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              <div className="cart-drawer__summary-row">
                <span>Shipping</span>
                <span>{shipping === 0 ? "Free" : `$${shipping.toFixed(2)}`}</span>
              </div>
              <div className="cart-drawer__summary-row">
                <span>Tax</span>
                <span>${tax.toFixed(2)}</span>
              </div>
              <div className="cart-drawer__summary-row cart-drawer__summary-row--total">
                <span>Total</span>
                <span>${total.toFixed(2)}</span>
              </div>

              {shipping > 0 && (
                <p className="cart-drawer__free-shipping-note">
                  Add ${(99 - subtotal).toFixed(2)} more for free shipping!
                </p>
              )}
            </div>

            {/* Actions */}
            <div className="cart-drawer__actions">
              <Link
                to="/checkout"
                className="cart-drawer__checkout-btn"
                onClick={onClose}
              >
                Proceed to Checkout
              </Link>
              <button
                className="cart-drawer__clear-btn"
                onClick={() => dispatch(clearCart())}
              >
                Clear Cart
              </button>
            </div>
          </>
        )}
      </aside>
    </>
  );
}
