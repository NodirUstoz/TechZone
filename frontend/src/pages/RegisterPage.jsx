/**
 * RegisterPage
 *
 * User registration form with client-side validation,
 * password strength feedback, and server error handling.
 */
import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import {
  FaUser,
  FaEnvelope,
  FaLock,
  FaSpinner,
  FaExclamationCircle,
  FaCheckCircle,
} from "react-icons/fa";

import {
  register,
  clearAuthError,
  selectIsAuthenticated,
  selectAuthLoading,
  selectAuthError,
} from "../store/slices/authSlice";

/**
 * Compute a password strength score from 0-4.
 */
function getPasswordStrength(password) {
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[a-z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score++;
  return Math.min(score, 4);
}

const strengthLabels = ["", "Weak", "Fair", "Good", "Strong"];
const strengthColors = ["", "#e74c3c", "#e67e22", "#f1c40f", "#27ae60"];

export default function RegisterPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const isAuthenticated = useSelector(selectIsAuthenticated);
  const loading = useSelector(selectAuthLoading);
  const serverError = useSelector(selectAuthError);

  const [formData, setFormData] = useState({
    email: "",
    username: "",
    password: "",
    confirmPassword: "",
    first_name: "",
    last_name: "",
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (serverError) dispatch(clearAuthError());
  }, [formData]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear individual field error on change
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.first_name.trim()) newErrors.first_name = "First name is required.";
    if (!formData.last_name.trim()) newErrors.last_name = "Last name is required.";
    if (!formData.username.trim()) {
      newErrors.username = "Username is required.";
    } else if (formData.username.length < 3) {
      newErrors.username = "Username must be at least 3 characters.";
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.username = "Username can only contain letters, numbers, and underscores.";
    }

    if (!formData.email.trim()) {
      newErrors.email = "Email is required.";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address.";
    }

    if (!formData.password) {
      newErrors.password = "Password is required.";
    } else if (getPasswordStrength(formData.password) < 3) {
      newErrors.password =
        "Password must be at least 8 characters with uppercase, lowercase, digit, and special character.";
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;

    dispatch(
      register({
        email: formData.email.trim(),
        username: formData.username.trim(),
        password: formData.password,
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
      })
    );
  };

  const passwordStrength = getPasswordStrength(formData.password);

  return (
    <div className="register-page">
      <div className="register-page__card">
        <div className="register-page__header">
          <h1>Create Account</h1>
          <p>Join TechZone and start shopping</p>
        </div>

        {serverError && (
          <div className="register-page__error">
            <FaExclamationCircle />
            <span>{serverError}</span>
          </div>
        )}

        <form className="register-page__form" onSubmit={handleSubmit} noValidate>
          {/* Name row */}
          <div className="register-page__row">
            <div className="register-page__field">
              <label htmlFor="first_name">First Name</label>
              <input
                id="first_name"
                name="first_name"
                type="text"
                value={formData.first_name}
                onChange={handleChange}
                placeholder="John"
                disabled={loading}
              />
              {errors.first_name && (
                <span className="register-page__field-error">{errors.first_name}</span>
              )}
            </div>

            <div className="register-page__field">
              <label htmlFor="last_name">Last Name</label>
              <input
                id="last_name"
                name="last_name"
                type="text"
                value={formData.last_name}
                onChange={handleChange}
                placeholder="Doe"
                disabled={loading}
              />
              {errors.last_name && (
                <span className="register-page__field-error">{errors.last_name}</span>
              )}
            </div>
          </div>

          {/* Username */}
          <div className="register-page__field">
            <label htmlFor="username">
              <FaUser className="register-page__field-icon" /> Username
            </label>
            <input
              id="username"
              name="username"
              type="text"
              value={formData.username}
              onChange={handleChange}
              placeholder="johndoe"
              autoComplete="username"
              disabled={loading}
            />
            {errors.username && (
              <span className="register-page__field-error">{errors.username}</span>
            )}
          </div>

          {/* Email */}
          <div className="register-page__field">
            <label htmlFor="email">
              <FaEnvelope className="register-page__field-icon" /> Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="john@example.com"
              autoComplete="email"
              disabled={loading}
            />
            {errors.email && (
              <span className="register-page__field-error">{errors.email}</span>
            )}
          </div>

          {/* Password */}
          <div className="register-page__field">
            <label htmlFor="password">
              <FaLock className="register-page__field-icon" /> Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Create a strong password"
              autoComplete="new-password"
              disabled={loading}
            />
            {formData.password && (
              <div className="register-page__strength">
                <div
                  className="register-page__strength-bar"
                  style={{
                    width: `${(passwordStrength / 4) * 100}%`,
                    backgroundColor: strengthColors[passwordStrength],
                  }}
                />
                <span style={{ color: strengthColors[passwordStrength] }}>
                  {strengthLabels[passwordStrength]}
                </span>
              </div>
            )}
            {errors.password && (
              <span className="register-page__field-error">{errors.password}</span>
            )}
          </div>

          {/* Confirm password */}
          <div className="register-page__field">
            <label htmlFor="confirmPassword">
              <FaLock className="register-page__field-icon" /> Confirm Password
            </label>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Repeat your password"
              autoComplete="new-password"
              disabled={loading}
            />
            {formData.confirmPassword && formData.password === formData.confirmPassword && (
              <span className="register-page__match-icon">
                <FaCheckCircle style={{ color: "#27ae60" }} /> Passwords match
              </span>
            )}
            {errors.confirmPassword && (
              <span className="register-page__field-error">{errors.confirmPassword}</span>
            )}
          </div>

          <button
            type="submit"
            className="register-page__submit-btn"
            disabled={loading}
          >
            {loading ? (
              <>
                <FaSpinner className="spinner" /> Creating account...
              </>
            ) : (
              "Create Account"
            )}
          </button>
        </form>

        <div className="register-page__footer">
          <p>
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
