import type { IconName } from "../icons/iconPaths";

export type ScreenId =
  | "feed"
  | "registry"
  | "detail"
  | "eval"
  | "escalation"
  | "settings";

export type RunStatus =
  | "Running"
  | "Completed"
  | "Escalated"
  | "Failed";

export type RunFilter = "All runs" | RunStatus;

export type TagClass =
  | "tag-accent"
  | "tag-accent-2"
  | "tag-neutral"
  | "tag-outline";

export type TriageRun = {
  id: number;
  leadName: string;
  company: string;
  agent: string;
  started: string;
  status: RunStatus;
  tagClass: TagClass;
  stage: number;
};

export type AgentRecord = {
  name: string;
  role: string;
  model: string;
  status: string;
  statusClass: TagClass;
  runsToday: number;
  tools: IconName[];
};

export type TraceStep = {
  title: string;
  time: string;
  duration: string;
  icon: IconName;
  done: boolean;
  payload: string | null;
};

export type EvalMetric = {
  label: string;
  value: string;
  trend: string;
  up: boolean;
};

export type EvalCase = {
  name: string;
  category: string;
  result: "Pass" | "Fail";
  latency: string;
};

export type EscalationItem = {
  leadName: string;
  company: string;
  reason: string;
  age: string;
  risk: "High" | "Medium" | "Low";
  riskClass: TagClass;
};

export type IntegrationItem = {
  name: string;
  icon: IconName;
  account: string;
  status: "Connected" | "Disconnected";
  statusClass: TagClass;
  actionLabel: string;
};

export type NavItem = {
  key: ScreenId;
  label: string;
  icon: IconName;
};

export type FeedStat = {
  num: string;
  label: string;
  trend: string;
  up: boolean;
  icon: IconName;
  iconBg: string;
  iconFg: string;
};

export type ScreenMeta = {
  title: string;
  description: string;
  headerAction: string | null;
};
