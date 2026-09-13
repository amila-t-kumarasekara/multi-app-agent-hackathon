"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { RunFilter, ScreenId } from "../types";

export type LeadTriageNavigation = {
  screen: ScreenId;
  filter: RunFilter;
  selectedRunId: string | null;
  setScreen: (screen: ScreenId) => void;
  setFilter: (filter: RunFilter) => void;
  openRunDetail: (runId: string) => void;
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
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  const setScreen = useCallback((next: ScreenId) => {
    setScreenState(next);
  }, []);

  const openRunDetail = useCallback((runId: string) => {
    setSelectedRunId(runId);
    setScreenState("detail");
  }, []);

  const value = useMemo(
    () => ({
      screen,
      filter,
      selectedRunId,
      setScreen,
      setFilter,
      openRunDetail,
    }),
    [screen, filter, selectedRunId, setScreen, openRunDetail],
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
