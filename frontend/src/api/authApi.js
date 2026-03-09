/**
 * Authentication API Service
 *
 * Functions for user registration, login, profile management,
 * and token refresh.
 */
import axiosClient, { setAuthTokens, clearAuthTokens } from "./axiosClient";

const authApi = {
  /**
   * Register a new user account.
   *
   * @param {Object} userData - Registration data.
   * @param {string} userData.email - Email address.
   * @param {string} userData.username - Username.
   * @param {string} userData.password - Password.
   * @param {string} userData.first_name - First name.
   * @param {string} userData.last_name - Last name.
   * @returns {Promise<Object>} User data and tokens.
   */
  async register(userData) {
    const { data } = await axiosClient.post("/auth/register", userData);
    setAuthTokens(data.access_token, data.refresh_token);
    return data;
  },

  /**
   * Log in with email and password.
   *
   * @param {string} email - User email.
   * @param {string} password - User password.
   * @returns {Promise<Object>} User data and tokens.
   */
  async login(email, password) {
    const { data } = await axiosClient.post("/auth/login", { email, password });
    setAuthTokens(data.access_token, data.refresh_token);
    return data;
  },

  /**
   * Log out the current user by clearing stored tokens.
   */
  logout() {
    clearAuthTokens();
  },

  /**
   * Fetch the currently authenticated user's profile.
   *
   * @returns {Promise<Object>} User profile data.
   */
  async getProfile() {
    const { data } = await axiosClient.get("/auth/me");
    return data.user;
  },

  /**
   * Update the current user's profile.
   *
   * @param {Object} updates - Fields to update.
   * @returns {Promise<Object>} Updated user data.
   */
  async updateProfile(updates) {
    const { data } = await axiosClient.put("/auth/me", updates);
    return data.user;
  },

  /**
   * Change the current user's password.
   *
   * @param {string} currentPassword - The current password.
   * @param {string} newPassword - The new password.
   * @returns {Promise<Object>} Updated user data.
   */
  async changePassword(currentPassword, newPassword) {
    const { data } = await axiosClient.put("/auth/me", {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return data.user;
  },

  /**
   * Check whether a user is currently authenticated
   * by looking for a stored access token.
   *
   * @returns {boolean}
   */
  isAuthenticated() {
    return !!localStorage.getItem("access_token");
  },
};

export default authApi;
