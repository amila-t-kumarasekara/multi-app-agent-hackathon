"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { RUNS } from "../data/mockData";
import type { RunFilter, ScreenId } from "../types";

export type LeadTriageNavigation = {
  screen: ScreenId;
  filter: RunFilter;
  setScreen: (screen: ScreenId) => void;
  setFilter: (filter: RunFilter) => void;
  openRunDetail: () => void;
};

const LeadTriageNavigationContext =
  createContext<LeadTriageNavigation | null>(null);

export function LeadTriageNavigationProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [screen, setScreenState] = useState<ScreenId>("feed");
  const [filter, setFilter] = useState<RunFilter>("All runs");

  const setScreen = useCallback((next: ScreenId) => {
    setScreenState(next);
  }, []);

  const openRunDetail = useCallback(() => {
    setScreenState("detail");
  }, []);

  const value = useMemo(
    () => ({
      screen,
      filter,
      setScreen,
      setFilter,
      openRunDetail,
    }),
    [screen, filter, setScreen, openRunDetail],
  );

  return (
    <LeadTriageNavigationContext.Provider value={value}>
      {children}
    </LeadTriageNavigationContext.Provider>
  );
}

export function useLeadTriageNavigation(): LeadTriageNavigation {
  const ctx = useContext(LeadTriageNavigationContext);
  if (!ctx) {
    throw new Error(
      "useLeadTriageNavigation must be used within LeadTriageNavigationProvider",
    );
  }
  return ctx;
}

/** Filters runs for the live feed without coupling list UI to filter state shape. */
export function useFilteredRuns() {
  const { filter } = useLeadTriageNavigation();
  return useMemo(
    () =>
      RUNS.filter(
        (run) => filter === "All runs" || run.status === filter,
      ),
    [filter],
  );
}
