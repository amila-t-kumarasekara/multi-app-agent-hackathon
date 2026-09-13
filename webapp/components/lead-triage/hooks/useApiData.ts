"use client";

import { useEffect, useRef, useState } from "react";

export type ApiDataState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
};

/** Polls `fetcher` on an interval and exposes the latest result. Pass `null` for fetcher to skip fetching. */
export function useApiData<T>(
  fetcher: (() => Promise<T>) | null,
  intervalMs = 5000,
): ApiDataState<T> {
  const [state, setState] = useState<ApiDataState<T>>({
    data: null,
    loading: fetcher !== null,
    error: null,
  });
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  useEffect(() => {
    if (!fetcher) {
      setState({ data: null, loading: false, error: null });
      return;
    }

    let cancelled = false;

    async function load(isFirst: boolean) {
      if (isFirst) setState((s) => ({ ...s, loading: true }));
      try {
        const data = await fetcherRef.current!();
        if (!cancelled) setState({ data, loading: false, error: null });
      } catch (e) {
        if (!cancelled) {
          setState((s) => ({
            data: s.data,
            loading: false,
            error: e instanceof Error ? e.message : "Failed to load",
          }));
        }
      }
    }

    load(true);
    const id = setInterval(() => load(false), intervalMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, fetcher === null]);

  return state;
}
