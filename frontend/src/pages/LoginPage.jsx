/**
 * LoginPage
 *
 * User login form with email/password fields, validation,
 * error display, and links to registration and password reset.
 */
import React, { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { FaEnvelope, FaLock, FaSpinner, FaExclamationCircle } from "react-icons/fa";

import {
  login,
  clearAuthError,
  selectIsAuthenticated,
  selectAuthLoading,
  selectAuthError,
} from "../store/slices/authSlice";

export default function LoginPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();

  const isAuthenticated = useSelector(selectIsAuthenticated);
  const loading = useSelector(selectAuthLoading);
  const serverError = useSelector(selectAuthError);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [validationError, setValidationError] = useState("");

  // Redirect after successful login
  const redirectTo = location.state?.from?.pathname || "/";

  useEffect(() => {
    if (isAuthenticated) {
      navigate(redirectTo, { replace: true });
    }
  }, [isAuthenticated, navigate, redirectTo]);

  // Clear errors when inputs change
  useEffect(() => {
    if (serverError) dispatch(clearAuthError());
    setValidationError("");
  }, [email, password]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Client-side validation
    if (!email.trim()) {
      setValidationError("Email is required.");
      return;
    }
    if (!password) {
      setValidationError("Password is required.");
      return;
    }

    dispatch(login({ email: email.trim(), password }));
  };

  const displayError = validationError || serverError;

  return (
    <div className="login-page">
      <div className="login-page__card">
        <div className="login-page__header">
          <h1>Sign In</h1>
          <p>Welcome back to TechZone</p>
        </div>

        {displayError && (
          <div className="login-page__error">
            <FaExclamationCircle />
            <span>{displayError}</span>
          </div>
        )}

        <form className="login-page__form" onSubmit={handleSubmit} noValidate>
          <div className="login-page__field">
            <label htmlFor="email">Email Address</label>
            <div className="login-page__input-wrapper">
              <FaEnvelope className="login-page__input-icon" />
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                autoFocus
                disabled={loading}
              />
            </div>
          </div>

          <div className="login-page__field">
            <label htmlFor="password">Password</label>
            <div className="login-page__input-wrapper">
              <FaLock className="login-page__input-icon" />
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                autoComplete="current-password"
                disabled={loading}
              />
            </div>
          </div>

          <button
            type="submit"
            className="login-page__submit-btn"
            disabled={loading}
          >
            {loading ? (
              <>
                <FaSpinner className="spinner" /> Signing in...
              </>
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        <div className="login-page__footer">
          <p>
            Don't have an account?{" "}
            <Link to="/register">Create one</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
