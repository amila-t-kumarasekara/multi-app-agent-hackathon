export function initialsFromName(fullName: string): string {
  return fullName
    .split(" ")
    .map((word) => word[0])
    .join("");
}

import type { CSSProperties } from "react";

export function trendChipStyle(up: boolean): CSSProperties {
  return {
    background: up ? "var(--color-accent-2-100)" : "var(--color-accent-100)",
    color: up ? "var(--color-accent-2-800)" : "var(--color-accent-800)",
  };
}

/** Formats a Unix timestamp (seconds) as a short relative-time string, e.g. "4m ago". */
export function formatRelativeTime(unixSeconds: number): string {
  const diffMs = Date.now() - unixSeconds * 1000;
  const diffSec = Math.max(0, Math.round(diffMs / 1000));
  if (diffSec < 60) return "just now";
  const diffMin = Math.round(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.round(diffHr / 24);
  return `${diffDay}d ago`;
}
