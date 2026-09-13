import type { TagClass } from "../types";

type StatusTagProps = {
  label: string;
  tagClass: TagClass;
};

export function StatusTag({ label, tagClass }: StatusTagProps) {
  return <span className={`tag ${tagClass}`}>{label}</span>;
}
