/**
 * Cart Slice
 *
 * Manages the shopping cart state with localStorage persistence.
 * Handles adding, removing, and updating item quantities.
 */
import { createSlice } from "@reduxjs/toolkit";

// ----------------------------------------------------------------
// LocalStorage persistence helpers
// ----------------------------------------------------------------

const CART_STORAGE_KEY = "techzone_cart";

function loadCartFromStorage() {
  try {
    const serialized = localStorage.getItem(CART_STORAGE_KEY);
    if (!serialized) return [];
    const items = JSON.parse(serialized);
    return Array.isArray(items) ? items : [];
  } catch {
    return [];
  }
}

function saveCartToStorage(items) {
  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
  } catch {
    // Silently fail if storage is full or unavailable
  }
}

// ----------------------------------------------------------------
// Helper calculations
// ----------------------------------------------------------------

function calculateTotals(items) {
  const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);
  const subtotal = items.reduce(
    (sum, item) => sum + item.price * item.quantity,
    0
  );
  const FREE_SHIPPING_THRESHOLD = 99.0;
  const FLAT_SHIPPING = 9.99;
  const TAX_RATE = 0.08;

  const shipping = subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : FLAT_SHIPPING;
  const tax = parseFloat((subtotal * TAX_RATE).toFixed(2));
  const total = parseFloat((subtotal + shipping + tax).toFixed(2));

  return { itemCount, subtotal, shipping, tax, total };
}

// ----------------------------------------------------------------
// Slice
// ----------------------------------------------------------------

const persistedItems = loadCartFromStorage();

const initialState = {
  items: persistedItems,
  ...calculateTotals(persistedItems),
};

const cartSlice = createSlice({
  name: "cart",
  initialState,

  reducers: {
    /**
     * Add a product to the cart or increment its quantity.
     *
     * Payload: { id, name, price, image_url, sku, max_quantity }
     */
    addToCart(state, action) {
      const { id, name, price, image_url, sku, max_quantity } = action.payload;
      const existing = state.items.find((item) => item.id === id);

      if (existing) {
        const cap = max_quantity || 99;
        existing.quantity = Math.min(existing.quantity + 1, cap);
      } else {
        state.items.push({
          id,
          name,
          price,
          image_url: image_url || null,
          sku: sku || "",
          quantity: 1,
          max_quantity: max_quantity || 99,
        });
      }

      Object.assign(state, calculateTotals(state.items));
      saveCartToStorage(state.items);
    },

    /**
     * Remove a product from the cart entirely.
     *
     * Payload: product id (number)
     */
    removeFromCart(state, action) {
      const productId = action.payload;
      state.items = state.items.filter((item) => item.id !== productId);
      Object.assign(state, calculateTotals(state.items));
      saveCartToStorage(state.items);
    },

    /**
     * Set a specific quantity for an item in the cart.
     *
     * Payload: { id, quantity }
     */
    updateQuantity(state, action) {
      const { id, quantity } = action.payload;
      const item = state.items.find((i) => i.id === id);

      if (item) {
        const newQty = Math.max(1, Math.min(quantity, item.max_quantity));
        item.quantity = newQty;
      }

      Object.assign(state, calculateTotals(state.items));
      saveCartToStorage(state.items);
    },

    /**
     * Increment the quantity of a cart item by one.
     *
     * Payload: product id (number)
     */
    incrementQuantity(state, action) {
      const item = state.items.find((i) => i.id === action.payload);
      if (item && item.quantity < item.max_quantity) {
        item.quantity += 1;
      }
      Object.assign(state, calculateTotals(state.items));
      saveCartToStorage(state.items);
    },

    /**
     * Decrement the quantity of a cart item by one.
     * Removes the item if quantity reaches zero.
     *
     * Payload: product id (number)
     */
    decrementQuantity(state, action) {
      const item = state.items.find((i) => i.id === action.payload);
      if (item) {
        item.quantity -= 1;
        if (item.quantity <= 0) {
          state.items = state.items.filter((i) => i.id !== action.payload);
        }
      }
      Object.assign(state, calculateTotals(state.items));
      saveCartToStorage(state.items);
    },

    /**
     * Clear all items from the cart.
     */
    clearCart(state) {
      state.items = [];
      Object.assign(state, calculateTotals([]));
      saveCartToStorage([]);
    },
  },
});

export const {
  addToCart,
  removeFromCart,
  updateQuantity,
  incrementQuantity,
  decrementQuantity,
  clearCart,
} = cartSlice.actions;

// Selectors
export const selectCartItems = (state) => state.cart.items;
export const selectCartItemCount = (state) => state.cart.itemCount;
export const selectCartSubtotal = (state) => state.cart.subtotal;
export const selectCartShipping = (state) => state.cart.shipping;
export const selectCartTax = (state) => state.cart.tax;
export const selectCartTotal = (state) => state.cart.total;
export const selectIsInCart = (productId) => (state) =>
  state.cart.items.some((item) => item.id === productId);

export default cartSlice.reducer;
