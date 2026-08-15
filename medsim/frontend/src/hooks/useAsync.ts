/**
 * Data-fetching hooks.
 *
 * Deliberately small and dependency-free rather than react-query: this app has
 * four endpoints and no mutations from the UI, so a cache library would be more
 * machinery than the problem needs. What it *does* implement carefully are the
 * three things that actually break in a QA harness:
 *
 *   - **Abort on unmount and on re-query**, so a slow response for filter state
 *     A cannot land after filter state B and repaint stale rows. The chaos
 *     latency header makes this trivially reproducible, and it is the single
 *     most common React data bug.
 *   - **Keeping the previous data visible while refetching**, so changing a
 *     filter does not flash the whole grid to skeletons.
 *   - **Distinguishing "never loaded" from "reloading"**, because those are
 *     different screens.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { ApiAbortError } from '../api/client';

export interface AsyncState<T> {
  data: T | null;
  error: unknown;
  /** True only before the first successful load. */
  loading: boolean;
  /** True while a refetch is in flight with data already on screen. */
  refreshing: boolean;
  reload: () => void;
}

export function useAsync<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  deps: readonly unknown[],
): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [nonce, setNonce] = useState(0);

  // Held in a ref so `reload` is stable and does not itself retrigger the
  // effect - a classic infinite-loop source.
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const hasData = data !== null;

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    if (hasData) setRefreshing(true);
    else setLoading(true);

    fetcherRef
      .current(controller.signal)
      .then((result) => {
        if (cancelled) return;
        setData(result);
        setError(null);
      })
      .catch((caught: unknown) => {
        // An abort is our own doing, never the user's problem.
        if (cancelled || caught instanceof ApiAbortError) return;
        setError(caught);
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
        setRefreshing(false);
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  return { data, error, loading, refreshing, reload };
}

/**
 * Debounce, used for the search box.
 *
 * 250 ms is chosen deliberately: below about 150 ms a fast typist still fires a
 * request per keystroke, and above about 400 ms the field feels laggy. The
 * Cypress suite asserts that typing a nine-character query issues one request,
 * not nine.
 */
export function useDebounced<T>(value: T, delayMs = 250): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(id);
  }, [value, delayMs]);

  return debounced;
}

/**
 * Tracks connectivity so the UI can distinguish "the server is broken" from
 * "you are on a train". The Phase 3 ADB scripts toggle airplane mode on a real
 * device to exercise this path.
 */
export function useOnline(): boolean {
  const [online, setOnline] = useState(() => navigator.onLine);

  useEffect(() => {
    const goOnline = () => setOnline(true);
    const goOffline = () => setOnline(false);
    window.addEventListener('online', goOnline);
    window.addEventListener('offline', goOffline);
    return () => {
      window.removeEventListener('online', goOnline);
      window.removeEventListener('offline', goOffline);
    };
  }, []);

  return online;
}

/**
 * Measures an element, so the SVG charts can be genuinely responsive rather
 * than relying on a fixed viewBox that letterboxes on a phone.
 */
export function useElementWidth<T extends HTMLElement>(): [React.RefObject<T>, number] {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    // ResizeObserver is absent in some locked-down Android WebViews; falling
    // back to the initial measurement keeps the chart rendered rather than
    // collapsed to zero width.
    if (typeof ResizeObserver === 'undefined') {
      setWidth(element.getBoundingClientRect().width);
      return;
    }

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) setWidth(entry.contentRect.width);
    });
    observer.observe(element);
    setWidth(element.getBoundingClientRect().width);
    return () => observer.disconnect();
  }, []);

  return [ref, width];
}
