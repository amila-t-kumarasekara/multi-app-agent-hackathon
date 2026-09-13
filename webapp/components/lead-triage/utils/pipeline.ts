import type { CSSProperties } from "react";
import type { IconName } from "../icons/iconPaths";
import { STAGE_ICONS } from "../data/mockData";

export type PipelineSegment =
  | { kind: "connector"; style: CSSProperties }
  | { kind: "step"; name: IconName; style: CSSProperties };

export function stepStyle(idx: number, stage: number): CSSProperties {
  if (idx < stage) {
    return { background: "var(--color-accent-2-500)", color: "white" };
  }
  if (idx === stage) {
    return { background: "var(--color-accent)", color: "white" };
  }
  return {
    background: "var(--color-neutral-200)",
    color: "var(--color-neutral-600)",
  };
}

export function connStyle(idx: number, stage: number): CSSProperties {
  return idx < stage
    ? { background: "var(--color-accent-2-500)" }
    : { background: "var(--color-neutral-200)" };
}

export function buildPipelineSegments(stage: number): PipelineSegment[] {
  const segments: PipelineSegment[] = [];

  STAGE_ICONS.forEach((iconName, i) => {
    if (i > 0) {
      segments.push({ kind: "connector", style: connStyle(i, stage) });
    }
    segments.push({ kind: "step", name: iconName, style: stepStyle(i, stage) });
  });

  return segments;
}
