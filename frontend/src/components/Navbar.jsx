/**
 * Navbar Component
 *
 * Top navigation bar with logo, search, cart icon, and auth links.
 */
import React, { useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import {
  FaShoppingCart,
  FaSearch,
  FaUser,
  FaSignOutAlt,
  FaBars,
  FaTimes,
} from "react-icons/fa";

import { selectIsAuthenticated, selectUser, logout } from "../store/slices/authSlice";
import { selectCartItemCount } from "../store/slices/cartSlice";
import useDebounce from "../hooks/useDebounce";

export default function Navbar() {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const isAuthenticated = useSelector(selectIsAuthenticated);
  const user = useSelector(selectUser);
  const cartItemCount = useSelector(selectCartItemCount);

  const [searchQuery, setSearchQuery] = useState("");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleSearchSubmit = useCallback(
    (e) => {
      e.preventDefault();
      const trimmed = searchQuery.trim();
      if (trimmed) {
        navigate(`/search?q=${encodeURIComponent(trimmed)}`);
        setSearchQuery("");
        setMobileMenuOpen(false);
      }
    },
    [searchQuery, navigate]
  );

  const handleLogout = () => {
    dispatch(logout());
    navigate("/");
    setMobileMenuOpen(false);
  };

  const toggleMobileMenu = () => {
    setMobileMenuOpen((prev) => !prev);
  };

  return (
    <nav className="navbar">
      <div className="navbar__container">
        {/* Logo */}
        <Link to="/" className="navbar__logo">
          <span className="navbar__logo-text">TechZone</span>
        </Link>

        {/* Search bar */}
        <form className="navbar__search" onSubmit={handleSearchSubmit}>
          <input
            type="text"
            className="navbar__search-input"
            placeholder="Search electronics..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="Search products"
          />
          <button type="submit" className="navbar__search-btn" aria-label="Search">
            <FaSearch />
          </button>
        </form>

        {/* Desktop nav links */}
        <div className={`navbar__links ${mobileMenuOpen ? "navbar__links--open" : ""}`}>
          <Link to="/products" className="navbar__link" onClick={() => setMobileMenuOpen(false)}>
            Products
          </Link>
          <Link to="/categories" className="navbar__link" onClick={() => setMobileMenuOpen(false)}>
            Categories
          </Link>

          {/* Cart */}
          <Link to="/cart" className="navbar__link navbar__cart-link" onClick={() => setMobileMenuOpen(false)}>
            <FaShoppingCart />
            {cartItemCount > 0 && (
              <span className="navbar__cart-badge">{cartItemCount}</span>
            )}
          </Link>

          {/* Auth links */}
          {isAuthenticated ? (
            <>
              <Link to="/account" className="navbar__link" onClick={() => setMobileMenuOpen(false)}>
                <FaUser />
                <span className="navbar__username">
                  {user?.first_name || "Account"}
                </span>
              </Link>
              {user?.role === "admin" && (
                <Link to="/admin" className="navbar__link" onClick={() => setMobileMenuOpen(false)}>
                  Admin
                </Link>
              )}
              <button className="navbar__link navbar__logout-btn" onClick={handleLogout}>
                <FaSignOutAlt />
                <span>Logout</span>
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="navbar__link" onClick={() => setMobileMenuOpen(false)}>
                Sign In
              </Link>
              <Link to="/register" className="navbar__link navbar__link--cta" onClick={() => setMobileMenuOpen(false)}>
                Sign Up
              </Link>
            </>
          )}
        </div>

        {/* Mobile menu toggle */}
        <button className="navbar__mobile-toggle" onClick={toggleMobileMenu} aria-label="Toggle menu">
          {mobileMenuOpen ? <FaTimes /> : <FaBars />}
        </button>
      </div>
    </nav>
  );
}
