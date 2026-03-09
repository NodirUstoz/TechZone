/**
 * useDebounce Hook
 *
 * Debounces a value so that the returned value only updates after
 * the specified delay has passed since the last change. Useful for
 * search inputs to avoid firing API calls on every keystroke.
 *
 * @param {*} value - The value to debounce.
 * @param {number} delay - Delay in milliseconds (default 300ms).
 * @returns {*} The debounced value.
 *
 * @example
 *   const [query, setQuery] = useState("");
 *   const debouncedQuery = useDebounce(query, 400);
 *
 *   useEffect(() => {
 *     if (debouncedQuery) {
 *       dispatch(searchProducts({ query: debouncedQuery }));
 *     }
 *   }, [debouncedQuery]);
 */
import { useState, useEffect } from "react";

export default function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}
