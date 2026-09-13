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
