/**
 * Product API Service
 *
 * Functions for fetching products, categories, brands, and search.
 */
import axiosClient from "./axiosClient";

const productApi = {
  /**
   * Fetch a paginated list of products with optional filters.
   *
   * @param {Object} [params] - Query parameters.
   * @param {number} [params.page=1] - Page number.
   * @param {number} [params.per_page=20] - Items per page.
   * @param {number} [params.category_id] - Filter by category.
   * @param {number} [params.brand_id] - Filter by brand.
   * @param {number} [params.min_price] - Minimum price.
   * @param {number} [params.max_price] - Maximum price.
   * @param {boolean} [params.in_stock] - Only in-stock items.
   * @param {boolean} [params.is_featured] - Only featured items.
   * @param {string} [params.sort="created_at"] - Sort field.
   * @param {string} [params.order="desc"] - Sort order.
   * @returns {Promise<Object>} Paginated product list.
   */
  async getProducts(params = {}) {
    const { data } = await axiosClient.get("/products", { params });
    return data;
  },

  /**
   * Fetch a single product by ID with full details.
   *
   * @param {number} productId - The product ID.
   * @returns {Promise<Object>} Product data with specs and images.
   */
  async getProduct(productId) {
    const { data } = await axiosClient.get(`/products/${productId}`);
    return data.product;
  },

  /**
   * Search products by query string.
   *
   * @param {string} query - Search query text.
   * @param {Object} [params] - Additional params (page, per_page).
   * @returns {Promise<Object>} Search results.
   */
  async searchProducts(query, params = {}) {
    const { data } = await axiosClient.get("/products/search", {
      params: { q: query, ...params },
    });
    return data;
  },

  /**
   * Fetch all active categories.
   *
   * @param {boolean} [includeChildren=false] - Include subcategories.
   * @returns {Promise<Array>} List of categories.
   */
  async getCategories(includeChildren = false) {
    const { data } = await axiosClient.get("/categories", {
      params: { include_children: includeChildren },
    });
    return data.categories;
  },

  /**
   * Fetch products within a specific category.
   *
   * @param {number} categoryId - Category ID.
   * @param {Object} [params] - Sorting and pagination params.
   * @returns {Promise<Object>} Category info and paginated products.
   */
  async getCategoryProducts(categoryId, params = {}) {
    const { data } = await axiosClient.get(
      `/categories/${categoryId}/products`,
      { params }
    );
    return data;
  },

  /**
   * Fetch all active brands.
   *
   * @returns {Promise<Array>} List of brands.
   */
  async getBrands() {
    const { data } = await axiosClient.get("/brands");
    return data.brands;
  },

  /**
   * Fetch reviews for a product.
   *
   * @param {number} productId - Product ID.
   * @param {Object} [params] - Pagination and filter params.
   * @returns {Promise<Object>} Paginated reviews.
   */
  async getProductReviews(productId, params = {}) {
    const { data } = await axiosClient.get(
      `/products/${productId}/reviews`,
      { params }
    );
    return data;
  },

  /**
   * Submit a review for a product.
   *
   * @param {number} productId - Product ID.
   * @param {Object} reviewData - Review data (rating, title, body, pros, cons).
   * @returns {Promise<Object>} Created review.
   */
  async submitReview(productId, reviewData) {
    const { data } = await axiosClient.post(
      `/products/${productId}/reviews`,
      reviewData
    );
    return data;
  },

  /**
   * Fetch the tech review for a product.
   *
   * @param {number} productId - Product ID.
   * @returns {Promise<Object|null>} Tech review data or null.
   */
  async getTechReview(productId) {
    try {
      const { data } = await axiosClient.get(
        `/products/${productId}/tech-review`
      );
      return data.tech_review;
    } catch (error) {
      if (error.response?.status === 404) return null;
      throw error;
    }
  },

  /**
   * Fetch price history for a product.
   *
   * @param {number} productId - Product ID.
   * @param {number} [days=90] - Number of days to look back.
   * @returns {Promise<Object>} Price history data.
   */
  async getPriceHistory(productId, days = 90) {
    const { data } = await axiosClient.get(
      `/products/${productId}/price-history`,
      { params: { days } }
    );
    return data;
  },
};

export default productApi;
