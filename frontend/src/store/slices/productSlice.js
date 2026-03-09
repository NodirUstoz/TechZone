/**
 * Product Slice
 *
 * Manages product listing, search, categories, and brands state.
 * Handles async data fetching via Redux Toolkit thunks.
 */
import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import productApi from "../../api/productApi";

// ----------------------------------------------------------------
// Async thunks
// ----------------------------------------------------------------

/**
 * Fetch paginated product list with filters.
 */
export const fetchProducts = createAsyncThunk(
  "products/fetchProducts",
  async (params = {}, { rejectWithValue }) => {
    try {
      return await productApi.getProducts(params);
    } catch (error) {
      return rejectWithValue(
        error.response?.data || { error: "Failed to fetch products." }
      );
    }
  }
);

/**
 * Fetch a single product by ID.
 */
export const fetchProductDetail = createAsyncThunk(
  "products/fetchProductDetail",
  async (productId, { rejectWithValue }) => {
    try {
      return await productApi.getProduct(productId);
    } catch (error) {
      return rejectWithValue(
        error.response?.data || { error: "Failed to fetch product." }
      );
    }
  }
);

/**
 * Search products by query.
 */
export const searchProducts = createAsyncThunk(
  "products/searchProducts",
  async ({ query, params = {} }, { rejectWithValue }) => {
    try {
      return await productApi.searchProducts(query, params);
    } catch (error) {
      return rejectWithValue(
        error.response?.data || { error: "Search failed." }
      );
    }
  }
);

/**
 * Fetch all categories.
 */
export const fetchCategories = createAsyncThunk(
  "products/fetchCategories",
  async (includeChildren = false, { rejectWithValue }) => {
    try {
      return await productApi.getCategories(includeChildren);
    } catch (error) {
      return rejectWithValue(
        error.response?.data || { error: "Failed to fetch categories." }
      );
    }
  }
);

/**
 * Fetch all brands.
 */
export const fetchBrands = createAsyncThunk(
  "products/fetchBrands",
  async (_, { rejectWithValue }) => {
    try {
      return await productApi.getBrands();
    } catch (error) {
      return rejectWithValue(
        error.response?.data || { error: "Failed to fetch brands." }
      );
    }
  }
);

// ----------------------------------------------------------------
// Slice
// ----------------------------------------------------------------

const initialState = {
  // Product list
  items: [],
  pagination: {
    page: 1,
    per_page: 20,
    total: 0,
    pages: 0,
    has_next: false,
    has_prev: false,
  },
  filters: {
    category_id: null,
    brand_id: null,
    min_price: null,
    max_price: null,
    in_stock: null,
    is_featured: null,
    sort: "created_at",
    order: "desc",
  },
  loading: false,
  error: null,

  // Single product detail
  currentProduct: null,
  detailLoading: false,
  detailError: null,

  // Search
  searchResults: [],
  searchQuery: "",
  searchTotal: 0,
  searchLoading: false,

  // Categories and brands
  categories: [],
  categoriesLoading: false,
  brands: [],
  brandsLoading: false,
};

const productSlice = createSlice({
  name: "products",
  initialState,

  reducers: {
    /**
     * Update filter values. Does not trigger a fetch -- the component
     * should dispatch fetchProducts after updating filters.
     */
    setFilters(state, action) {
      state.filters = { ...state.filters, ...action.payload };
    },

    /**
     * Reset all filters to defaults.
     */
    resetFilters(state) {
      state.filters = { ...initialState.filters };
    },

    /**
     * Clear the current product detail.
     */
    clearProductDetail(state) {
      state.currentProduct = null;
      state.detailError = null;
    },

    /**
     * Clear search results.
     */
    clearSearch(state) {
      state.searchResults = [];
      state.searchQuery = "";
      state.searchTotal = 0;
    },
  },

  extraReducers: (builder) => {
    // Fetch products
    builder.addCase(fetchProducts.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchProducts.fulfilled, (state, action) => {
      state.loading = false;
      state.items = action.payload.items;
      state.pagination = {
        page: action.payload.page,
        per_page: action.payload.per_page,
        total: action.payload.total,
        pages: action.payload.pages,
        has_next: action.payload.has_next,
        has_prev: action.payload.has_prev,
      };
    });
    builder.addCase(fetchProducts.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload?.error || "Failed to load products.";
    });

    // Fetch product detail
    builder.addCase(fetchProductDetail.pending, (state) => {
      state.detailLoading = true;
      state.detailError = null;
    });
    builder.addCase(fetchProductDetail.fulfilled, (state, action) => {
      state.detailLoading = false;
      state.currentProduct = action.payload;
    });
    builder.addCase(fetchProductDetail.rejected, (state, action) => {
      state.detailLoading = false;
      state.detailError = action.payload?.error || "Product not found.";
    });

    // Search products
    builder.addCase(searchProducts.pending, (state) => {
      state.searchLoading = true;
    });
    builder.addCase(searchProducts.fulfilled, (state, action) => {
      state.searchLoading = false;
      state.searchResults = action.payload.items || action.payload.products || [];
      state.searchTotal = action.payload.total || 0;
    });
    builder.addCase(searchProducts.rejected, (state) => {
      state.searchLoading = false;
      state.searchResults = [];
    });

    // Fetch categories
    builder.addCase(fetchCategories.pending, (state) => {
      state.categoriesLoading = true;
    });
    builder.addCase(fetchCategories.fulfilled, (state, action) => {
      state.categoriesLoading = false;
      state.categories = action.payload;
    });
    builder.addCase(fetchCategories.rejected, (state) => {
      state.categoriesLoading = false;
    });

    // Fetch brands
    builder.addCase(fetchBrands.pending, (state) => {
      state.brandsLoading = true;
    });
    builder.addCase(fetchBrands.fulfilled, (state, action) => {
      state.brandsLoading = false;
      state.brands = action.payload;
    });
    builder.addCase(fetchBrands.rejected, (state) => {
      state.brandsLoading = false;
    });
  },
});

export const { setFilters, resetFilters, clearProductDetail, clearSearch } =
  productSlice.actions;

// Selectors
export const selectProducts = (state) => state.products.items;
export const selectProductsPagination = (state) => state.products.pagination;
export const selectProductsLoading = (state) => state.products.loading;
export const selectProductsError = (state) => state.products.error;
export const selectFilters = (state) => state.products.filters;
export const selectCurrentProduct = (state) => state.products.currentProduct;
export const selectDetailLoading = (state) => state.products.detailLoading;
export const selectCategories = (state) => state.products.categories;
export const selectBrands = (state) => state.products.brands;
export const selectSearchResults = (state) => state.products.searchResults;
export const selectSearchLoading = (state) => state.products.searchLoading;

export default productSlice.reducer;
