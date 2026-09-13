import type {
  AgentRecord,
  EscalationItem,
  EvalCase,
  EvalMetric,
  FeedStat,
  IntegrationItem,
  NavItem,
  ScreenMeta,
  ScreenId,
  TraceStep,
  TriageRun,
} from "../types";

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

export const RUNS: TriageRun[] = [
  {
    id: 4821,
    leadName: "Priya Anand",
    company: "Verdant Foods",
    agent: "Triage-Alpha",
    started: "4m ago",
    status: "Running",
    tagClass: "tag-accent",
    stage: 3,
  },
  {
    id: 4820,
    leadName: "Marcus Webb",
    company: "Kettle & Co",
    agent: "Triage-Alpha",
    started: "11m ago",
    status: "Completed",
    tagClass: "tag-accent-2",
    stage: 5,
  },
  {
    id: 4819,
    leadName: "Sofia Reyes",
    company: "Northbridge Labs",
    agent: "Triage-Beta",
    started: "18m ago",
    status: "Escalated",
    tagClass: "tag-outline",
    stage: 2,
  },
  {
    id: 4818,
    leadName: "Tom Halvorsen",
    company: "Alder Studio",
    agent: "Triage-Alpha",
    started: "26m ago",
    status: "Completed",
    tagClass: "tag-accent-2",
    stage: 5,
  },
  {
    id: 4817,
    leadName: "Grace Lin",
    company: "Pinehill Group",
    agent: "Triage-Beta",
    started: "33m ago",
    status: "Failed",
    tagClass: "tag-outline",
    stage: 1,
  },
  {
    id: 4816,
    leadName: "Daniel Osei",
    company: "Merit Partners",
    agent: "Triage-Alpha",
    started: "41m ago",
    status: "Completed",
    tagClass: "tag-accent-2",
    stage: 5,
  },
];

export const AGENTS: AgentRecord[] = [
  {
    name: "Triage-Alpha",
    role: "Primary intake classifier",
    model: "Claude Opus 4.5",
    status: "Active",
    statusClass: "tag-accent-2",
    runsToday: 214,
    tools: ["mail", "database", "message", "calendar"],
  },
  {
    name: "Triage-Beta",
    role: "High-risk overflow handler",
    model: "Claude Opus 4.5",
    status: "Active",
    statusClass: "tag-accent-2",
    runsToday: 88,
    tools: ["mail", "database", "message"],
  },
  {
    name: "Enrichment-1",
    role: "CRM field enrichment",
    model: "Claude Haiku 4.5",
    status: "Active",
    statusClass: "tag-accent-2",
    runsToday: 302,
    tools: ["database"],
  },
  {
    name: "Scheduler-1",
    role: "Calendar & meeting drafting",
    model: "Claude Haiku 4.5",
    status: "Paused",
    statusClass: "tag-neutral",
    runsToday: 0,
    tools: ["calendar", "mail"],
  },
  {
    name: "Notifier-1",
    role: "Slack summary composer",
    model: "Claude Haiku 4.5",
    status: "Active",
    statusClass: "tag-accent-2",
    runsToday: 190,
    tools: ["message"],
  },
];

export const DETAIL_RUN = {
  id: 4821,
  leadName: "Priya Anand",
  company: "Verdant Foods",
  agent: "Triage-Alpha",
  duration: "8s",
};

export const DETAIL_STEPS: TraceStep[] = [
  {
    title: "Email received & parsed",
    time: "10:02:14",
    duration: "0.4s",
    icon: "mail",
    done: true,
    payload:
      'from: p.anand@verdantfoods.com · subject: "Bulk order inquiry — Q3"',
  },
  {
    title: "Intent classified: New lead, high value",
    time: "10:02:15",
    duration: "0.9s",
    icon: "bot",
    done: true,
    payload: "confidence: 0.94 · category: sales_inquiry",
  },
  {
    title: "CRM record enriched",
    time: "10:02:17",
    duration: "1.6s",
    icon: "database",
    done: true,
    payload: "matched account: Verdant Foods (existing, tier 2)",
  },
  {
    title: "Slack summary posted to #sales-leads",
    time: "10:02:19",
    duration: "0.7s",
    icon: "message",
    done: true,
    payload: null,
  },
  {
    title: "Calendar hold drafted for AE review",
    time: "10:02:22",
    duration: "in progress",
    icon: "calendar",
    done: false,
    payload: null,
  },
];

export const EVAL_METRICS: EvalMetric[] = [
  {
    label: "Overall pass rate",
    value: "96.2%",
    trend: "+1.1 pts vs last week",
    up: true,
  },
  {
    label: "Tool-call correctness",
    value: "98.4%",
    trend: "+0.3 pts",
    up: true,
  },
  {
    label: "Hallucination rate",
    value: "0.6%",
    trend: "-0.2 pts",
    up: true,
  },
  {
    label: "P95 latency",
    value: "3.1s",
    trend: "+0.4s",
    up: false,
  },
];

export const EVAL_CASES: EvalCase[] = [
  {
    name: "Ambiguous subject line routing",
    category: "Classification",
    result: "Pass",
    latency: "1.2s",
  },
  {
    name: "Duplicate lead de-duplication",
    category: "CRM write",
    result: "Pass",
    latency: "2.0s",
  },
  {
    name: "Non-English inquiry handling",
    category: "Classification",
    result: "Fail",
    latency: "4.8s",
  },
  {
    name: "Calendar conflict detection",
    category: "Scheduling",
    result: "Pass",
    latency: "1.6s",
  },
  {
    name: "Spam / phishing rejection",
    category: "Safety",
    result: "Pass",
    latency: "0.8s",
  },
  {
    name: "Multi-thread context carryover",
    category: "Memory",
    result: "Pass",
    latency: "2.4s",
  },
];

export const ESCALATIONS: EscalationItem[] = [
  {
    leadName: "Sofia Reyes",
    company: "Northbridge Labs",
    reason: "Ambiguous purchase intent",
    age: "18m ago",
    risk: "High",
    riskClass: "tag-outline",
  },
  {
    leadName: "Grace Lin",
    company: "Pinehill Group",
    reason: "CRM write conflict on existing record",
    age: "33m ago",
    risk: "High",
    riskClass: "tag-outline",
  },
  {
    leadName: "Ravi Chandran",
    company: "Ostro Analytics",
    reason: "Suspicious sender domain",
    age: "1h ago",
    risk: "Medium",
    riskClass: "tag-accent",
  },
  {
    leadName: "Elena Kowalski",
    company: "Birchwood Retail",
    reason: "Calendar double-booking detected",
    age: "2h ago",
    risk: "Medium",
    riskClass: "tag-accent",
  },
  {
    leadName: "Jamal Foster",
    company: "Coastline Ventures",
    reason: "Low-confidence intent classification",
    age: "3h ago",
    risk: "Low",
    riskClass: "tag-neutral",
  },
];

export const INTEGRATIONS: IntegrationItem[] = [
  {
    name: "Email (Gmail)",
    icon: "mail",
    account: "ops@furrow.ai · connected",
    status: "Connected",
    statusClass: "tag-accent-2",
    actionLabel: "Manage",
  },
  {
    name: "CRM (Salesforce)",
    icon: "database",
    account: "furrow-prod instance",
    status: "Connected",
    statusClass: "tag-accent-2",
    actionLabel: "Manage",
  },
  {
    name: "Slack",
    icon: "message",
    account: "#sales-leads workspace",
    status: "Connected",
    statusClass: "tag-accent-2",
    actionLabel: "Manage",
  },
  {
    name: "Google Calendar",
    icon: "calendar",
    account: "ops@furrow.ai",
    status: "Connected",
    statusClass: "tag-accent-2",
    actionLabel: "Manage",
  },
  {
    name: "HubSpot",
    icon: "database",
    account: "Not connected",
    status: "Disconnected",
    statusClass: "tag-neutral",
    actionLabel: "Connect",
  },
];

export const FEED_STATS: FeedStat[] = [
  {
    num: "214",
    label: "Runs today",
    trend: "+18 vs yesterday",
    up: true,
    icon: "activity",
    iconBg: "var(--color-accent-2-100)",
    iconFg: "var(--color-accent-2-800)",
  },
  {
    num: "96.2%",
    label: "Auto-resolved",
    trend: "+1.1 pts",
    up: true,
    icon: "check",
    iconBg: "var(--color-accent-2-100)",
    iconFg: "var(--color-accent-2-800)",
  },
  {
    num: "8",
    label: "In escalation",
    trend: "+3 vs yesterday",
    up: false,
    icon: "flag",
    iconBg: "var(--color-accent-100)",
    iconFg: "var(--color-accent-800)",
  },
  {
    num: "3.1s",
    label: "Avg. time to first action",
    trend: "+0.4s",
    up: false,
    icon: "clock",
    iconBg: "var(--color-accent-100)",
    iconFg: "var(--color-accent-800)",
  },
];

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
