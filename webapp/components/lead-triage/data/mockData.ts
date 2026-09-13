import type { NavItem, ScreenMeta, ScreenId } from "../types";

export const NAV_ITEMS: NavItem[] = [
  { key: "feed", label: "Live run feed", icon: "activity" },
  { key: "registry", label: "Agent registry", icon: "bot" },
  { key: "detail", label: "Run detail", icon: "clock" },
  { key: "eval", label: "Eval suite", icon: "check" },
  { key: "escalation", label: "Escalations", icon: "flag" },
  { key: "settings", label: "Integrations", icon: "gear" },
];

export const RUN_FILTERS = [
  "All runs",
  "Running",
  "Completed",
  "Escalated",
] as const;

export const STAGE_ICONS = [
  "mail",
  "bot",
  "database",
  "message",
  "calendar",
] as const;

const SCREEN_META: Record<ScreenId, ScreenMeta> = {
  feed: {
    title: "Live run feed",
    description:
      "Every inbound lead moving through email → agent → CRM → Slack → calendar, in real time.",
    headerAction: "New run",
  },
  registry: {
    title: "Agent registry",
    description:
      "Which agents are live, what model they run on, and which tools they can call.",
    headerAction: "Add agent",
  },
  detail: {
    title: "Run detail",
    description: "Full state-machine trace for a single lead-triage run.",
    headerAction: null,
  },
  eval: {
    title: "Eval suite results",
    description:
      "Automated evaluation coverage across classification, safety and scheduling.",
    headerAction: "Run eval suite",
  },
  escalation: {
    title: "Escalation & quarantine queue",
    description: "Runs a human needs to review before the agent continues.",
    headerAction: null,
  },
  settings: {
    title: "Integrations",
    description:
      "Connection status for every system the agents read from and write to.",
    headerAction: "Add integration",
  },
};

export function getScreenMeta(screen: ScreenId): ScreenMeta {
  return SCREEN_META[screen];
}
