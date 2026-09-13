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

export type NavItem = {
  key: ScreenId;
  label: string;
  icon: IconName;
};

export type ScreenMeta = {
  title: string;
  description: string;
  headerAction: string | null;
};
