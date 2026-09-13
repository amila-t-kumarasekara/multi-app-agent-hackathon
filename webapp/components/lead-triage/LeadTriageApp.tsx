"use client";

import { LeadTriageNavigationProvider } from "./context/LeadTriageNavigationContext";
import { LeadTriageShell } from "./layout/LeadTriageShell";
import { ScreenRouter } from "./screens/ScreenRouter";

export function LeadTriageApp() {
  return (
    <LeadTriageNavigationProvider>
      <LeadTriageShell>
        <ScreenRouter />
      </LeadTriageShell>
    </LeadTriageNavigationProvider>
  );
}
