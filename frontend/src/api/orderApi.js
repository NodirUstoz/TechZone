/**
 * Order API Service
 *
 * Functions for creating, viewing, and cancelling orders.
 */
import axiosClient from "./axiosClient";

const orderApi = {
  /**
   * Fetch the current user's orders with optional status filter.
   *
   * @param {Object} [params] - Query parameters.
   * @param {number} [params.page=1] - Page number.
   * @param {number} [params.per_page=20] - Items per page.
   * @param {string} [params.status] - Filter by order status.
   * @returns {Promise<Object>} Paginated order list.
   */
  async getOrders(params = {}) {
    const { data } = await axiosClient.get("/orders", { params });
    return data;
  },

  /**
   * Fetch a single order by ID.
   *
   * @param {number} orderId - The order ID.
   * @returns {Promise<Object>} Order data with items and payment.
   */
  async getOrder(orderId) {
    const { data } = await axiosClient.get(`/orders/${orderId}`);
    return data.order;
  },

  /**
   * Place a new order.
   *
   * @param {Object} orderData - Order data.
   * @param {Array<Object>} orderData.items - Array of { product_id, quantity }.
   * @param {Object} [orderData.shipping_address] - Shipping address.
   * @param {string} [orderData.customer_notes] - Optional notes.
   * @returns {Promise<Object>} Created order data.
   */
  async createOrder(orderData) {
    const { data } = await axiosClient.post("/orders", orderData);
    return data;
  },

  /**
   * Cancel an existing order.
   *
   * @param {number} orderId - The order ID to cancel.
   * @returns {Promise<Object>} Updated order data.
   */
  async cancelOrder(orderId) {
    const { data } = await axiosClient.put(`/orders/${orderId}/cancel`);
    return data;
  },

  /**
   * Fetch the user's comparison lists.
   *
   * @returns {Promise<Object>} Paginated comparison lists.
   */
  async getComparisons() {
    const { data } = await axiosClient.get("/comparisons");
    return data;
  },

  /**
   * Fetch the user's price alerts.
   *
   * @returns {Promise<Object>} Paginated price alerts.
   */
  async getPriceAlerts() {
    const { data } = await axiosClient.get("/price-alerts");
    return data;
  },

  /**
   * Create a price alert for a product.
   *
   * @param {number} productId - Product ID.
   * @param {number} targetPrice - Target price threshold.
   * @returns {Promise<Object>} Created alert data.
   */
  async createPriceAlert(productId, targetPrice) {
    const { data } = await axiosClient.post("/price-alerts", {
      product_id: productId,
      target_price: targetPrice,
    });
    return data;
  },

  /**
   * Delete a price alert.
   *
   * @param {number} alertId - Alert ID.
   * @returns {Promise<Object>} Deletion confirmation.
   */
  async deletePriceAlert(alertId) {
    const { data } = await axiosClient.delete(`/price-alerts/${alertId}`);
    return data;
  },

  /**
   * Fetch the user's warranty registrations.
   *
   * @param {Object} [params] - Query parameters.
   * @returns {Promise<Object>} Paginated warranties.
   */
  async getWarranties(params = {}) {
    const { data } = await axiosClient.get("/warranties", { params });
    return data;
  },

  /**
   * Register a product warranty.
   *
   * @param {Object} warrantyData - Warranty registration data.
   * @returns {Promise<Object>} Created warranty data.
   */
  async registerWarranty(warrantyData) {
    const { data } = await axiosClient.post("/warranties", warrantyData);
    return data;
  },
};

export default orderApi;
