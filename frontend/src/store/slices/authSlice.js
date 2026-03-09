/**
 * Auth Slice
 *
 * Manages authentication state: current user, login/register status,
 * and profile updates.
 */
import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import authApi from "../../api/authApi";

// ----------------------------------------------------------------
// Async thunks
// ----------------------------------------------------------------

/**
 * Register a new user account.
 */
export const register = createAsyncThunk(
  "auth/register",
  async (userData, { rejectWithValue }) => {
    try {
      const data = await authApi.register(userData);
      return data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data || { error: "Registration failed." }
      );
    }
  }
);

/**
 * Log in with email and password.
 */
export const login = createAsyncThunk(
  "auth/login",
  async ({ email, password }, { rejectWithValue }) => {
    try {
      const data = await authApi.login(email, password);
      return data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data || { error: "Login failed." }
      );
    }
  }
);

/**
 * Fetch the current user's profile (used on app load to restore session).
 */
export const fetchProfile = createAsyncThunk(
  "auth/fetchProfile",
  async (_, { rejectWithValue }) => {
    try {
      const user = await authApi.getProfile();
      return user;
    } catch (error) {
      return rejectWithValue(
        error.response?.data || { error: "Failed to fetch profile." }
      );
    }
  }
);

/**
 * Update the current user's profile fields.
 */
export const updateProfile = createAsyncThunk(
  "auth/updateProfile",
  async (updates, { rejectWithValue }) => {
    try {
      const user = await authApi.updateProfile(updates);
      return user;
    } catch (error) {
      return rejectWithValue(
        error.response?.data || { error: "Profile update failed." }
      );
    }
  }
);

// ----------------------------------------------------------------
// Slice
// ----------------------------------------------------------------

const initialState = {
  user: null,
  isAuthenticated: authApi.isAuthenticated(),
  loading: false,
  error: null,
  profileLoading: false,
};

const authSlice = createSlice({
  name: "auth",
  initialState,

  reducers: {
    /**
     * Log out: clear user state and tokens.
     */
    logout(state) {
      authApi.logout();
      state.user = null;
      state.isAuthenticated = false;
      state.error = null;
    },

    /**
     * Clear any auth errors from state.
     */
    clearAuthError(state) {
      state.error = null;
    },
  },

  extraReducers: (builder) => {
    // Register
    builder.addCase(register.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(register.fulfilled, (state, action) => {
      state.loading = false;
      state.user = action.payload.user;
      state.isAuthenticated = true;
    });
    builder.addCase(register.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload?.error || "Registration failed.";
    });

    // Login
    builder.addCase(login.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(login.fulfilled, (state, action) => {
      state.loading = false;
      state.user = action.payload.user;
      state.isAuthenticated = true;
    });
    builder.addCase(login.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload?.error || "Login failed.";
    });

    // Fetch profile
    builder.addCase(fetchProfile.pending, (state) => {
      state.profileLoading = true;
    });
    builder.addCase(fetchProfile.fulfilled, (state, action) => {
      state.profileLoading = false;
      state.user = action.payload;
      state.isAuthenticated = true;
    });
    builder.addCase(fetchProfile.rejected, (state) => {
      state.profileLoading = false;
      state.user = null;
      state.isAuthenticated = false;
    });

    // Update profile
    builder.addCase(updateProfile.pending, (state) => {
      state.profileLoading = true;
      state.error = null;
    });
    builder.addCase(updateProfile.fulfilled, (state, action) => {
      state.profileLoading = false;
      state.user = action.payload;
    });
    builder.addCase(updateProfile.rejected, (state, action) => {
      state.profileLoading = false;
      state.error = action.payload?.error || "Profile update failed.";
    });
  },
});

export const { logout, clearAuthError } = authSlice.actions;

// Selectors
export const selectUser = (state) => state.auth.user;
export const selectIsAuthenticated = (state) => state.auth.isAuthenticated;
export const selectAuthLoading = (state) => state.auth.loading;
export const selectAuthError = (state) => state.auth.error;
export const selectIsAdmin = (state) => state.auth.user?.role === "admin";

export default authSlice.reducer;
