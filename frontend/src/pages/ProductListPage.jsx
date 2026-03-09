/**
 * ProductListPage
 *
 * Main product listing page with sidebar filters, sort controls,
 * and paginated product grid.
 */
import React, { useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { FaFilter, FaTimes, FaSpinner } from "react-icons/fa";

import {
  fetchProducts,
  fetchCategories,
  fetchBrands,
  setFilters,
  resetFilters,
  selectProducts,
  selectProductsPagination,
  selectProductsLoading,
  selectFilters,
  selectCategories,
  selectBrands,
} from "../store/slices/productSlice";
import ProductCard from "../components/ProductCard";

export default function ProductListPage() {
  const dispatch = useDispatch();
  const [searchParams, setSearchParams] = useSearchParams();

  const products = useSelector(selectProducts);
  const pagination = useSelector(selectProductsPagination);
  const loading = useSelector(selectProductsLoading);
  const filters = useSelector(selectFilters);
  const categories = useSelector(selectCategories);
  const brands = useSelector(selectBrands);

  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  // Load categories and brands once
  useEffect(() => {
    dispatch(fetchCategories());
    dispatch(fetchBrands());
  }, [dispatch]);

  // Sync URL params to filters and fetch products
  useEffect(() => {
    const params = {
      page: parseInt(searchParams.get("page")) || 1,
      per_page: 20,
      category_id: searchParams.get("category_id") || null,
      brand_id: searchParams.get("brand_id") || null,
      min_price: searchParams.get("min_price") || null,
      max_price: searchParams.get("max_price") || null,
      in_stock: searchParams.get("in_stock") || null,
      sort: searchParams.get("sort") || "created_at",
      order: searchParams.get("order") || "desc",
    };

    dispatch(setFilters(params));
    dispatch(fetchProducts(params));
  }, [dispatch, searchParams]);

  const updateFilter = useCallback(
    (key, value) => {
      const newParams = new URLSearchParams(searchParams);
      if (value === null || value === "" || value === undefined) {
        newParams.delete(key);
      } else {
        newParams.set(key, value);
      }
      // Reset to page 1 when filters change
      if (key !== "page") {
        newParams.set("page", "1");
      }
      setSearchParams(newParams);
    },
    [searchParams, setSearchParams]
  );

  const handleResetFilters = () => {
    dispatch(resetFilters());
    setSearchParams({});
  };

  const goToPage = (page) => {
    updateFilter("page", page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="product-list-page">
      {/* Mobile filter toggle */}
      <button
        className="product-list-page__filter-toggle"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        <FaFilter /> Filters
      </button>

      {/* Sidebar filters */}
      <aside className={`product-list-page__sidebar ${sidebarOpen ? "product-list-page__sidebar--open" : ""}`}>
        <div className="product-list-page__sidebar-header">
          <h3>Filters</h3>
          <button onClick={() => setSidebarOpen(false)} className="product-list-page__sidebar-close">
            <FaTimes />
          </button>
        </div>

        {/* Category filter */}
        <div className="product-list-page__filter-group">
          <h4>Category</h4>
          <select
            value={filters.category_id || ""}
            onChange={(e) => updateFilter("category_id", e.target.value || null)}
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name} ({cat.product_count})
              </option>
            ))}
          </select>
        </div>

        {/* Brand filter */}
        <div className="product-list-page__filter-group">
          <h4>Brand</h4>
          <select
            value={filters.brand_id || ""}
            onChange={(e) => updateFilter("brand_id", e.target.value || null)}
          >
            <option value="">All Brands</option>
            {brands.map((brand) => (
              <option key={brand.id} value={brand.id}>
                {brand.name}
              </option>
            ))}
          </select>
        </div>

        {/* Price range */}
        <div className="product-list-page__filter-group">
          <h4>Price Range</h4>
          <div className="product-list-page__price-inputs">
            <input
              type="number"
              placeholder="Min"
              min="0"
              value={filters.min_price || ""}
              onChange={(e) => updateFilter("min_price", e.target.value || null)}
            />
            <span>-</span>
            <input
              type="number"
              placeholder="Max"
              min="0"
              value={filters.max_price || ""}
              onChange={(e) => updateFilter("max_price", e.target.value || null)}
            />
          </div>
        </div>

        {/* In stock toggle */}
        <div className="product-list-page__filter-group">
          <label>
            <input
              type="checkbox"
              checked={filters.in_stock === "true"}
              onChange={(e) =>
                updateFilter("in_stock", e.target.checked ? "true" : null)
              }
            />
            In Stock Only
          </label>
        </div>

        <button className="product-list-page__reset-btn" onClick={handleResetFilters}>
          Reset Filters
        </button>
      </aside>

      {/* Main content */}
      <main className="product-list-page__main">
        {/* Sort bar */}
        <div className="product-list-page__sort-bar">
          <span className="product-list-page__result-count">
            {pagination.total} product{pagination.total !== 1 ? "s" : ""} found
          </span>

          <div className="product-list-page__sort-controls">
            <label>Sort by:</label>
            <select
              value={filters.sort}
              onChange={(e) => updateFilter("sort", e.target.value)}
            >
              <option value="created_at">Newest</option>
              <option value="price">Price</option>
              <option value="name">Name</option>
            </select>
            <select
              value={filters.order}
              onChange={(e) => updateFilter("order", e.target.value)}
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
        </div>

        {/* Product grid */}
        {loading ? (
          <div className="product-list-page__loading">
            <FaSpinner className="spinner" /> Loading products...
          </div>
        ) : products.length === 0 ? (
          <div className="product-list-page__empty">
            <p>No products found matching your filters.</p>
            <button onClick={handleResetFilters}>Clear Filters</button>
          </div>
        ) : (
          <div className="product-list-page__grid">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}

        {/* Pagination */}
        {pagination.pages > 1 && (
          <div className="product-list-page__pagination">
            <button
              disabled={!pagination.has_prev}
              onClick={() => goToPage(pagination.page - 1)}
            >
              Previous
            </button>

            {Array.from({ length: pagination.pages }, (_, i) => i + 1)
              .filter((p) => {
                // Show first, last, and pages near current
                return (
                  p === 1 ||
                  p === pagination.pages ||
                  Math.abs(p - pagination.page) <= 2
                );
              })
              .map((p, idx, arr) => (
                <React.Fragment key={p}>
                  {idx > 0 && arr[idx - 1] !== p - 1 && <span className="product-list-page__ellipsis">...</span>}
                  <button
                    className={p === pagination.page ? "product-list-page__page--active" : ""}
                    onClick={() => goToPage(p)}
                  >
                    {p}
                  </button>
                </React.Fragment>
              ))}

            <button
              disabled={!pagination.has_next}
              onClick={() => goToPage(pagination.page + 1)}
            >
              Next
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
