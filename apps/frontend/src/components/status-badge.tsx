import type { ReactNode } from "react";

export type BadgeTone =
  | "neutral"
  | "success"
  | "warning"
  | "danger"
  | "info";

type StatusBadgeProps = {
  children: ReactNode;
  tone: BadgeTone;
};

export function StatusBadge({ children, tone }: StatusBadgeProps) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}
