import { StatusBadge, type BadgeTone } from "@/components/status-badge";

export type ConfidenceLevel =
  | "high"
  | "medium-high"
  | "medium"
  | "low"
  | "review";

const CONFIDENCE_TONES: Record<ConfidenceLevel, BadgeTone> = {
  high: "success",
  "medium-high": "info",
  medium: "warning",
  low: "danger",
  review: "warning",
};

const CONFIDENCE_LABELS: Record<ConfidenceLevel, string> = {
  high: "High confidence",
  "medium-high": "Medium-high confidence",
  medium: "Medium confidence",
  low: "Low confidence",
  review: "Needs review",
};

type ConfidenceBadgeProps = {
  level: ConfidenceLevel;
};

export function ConfidenceBadge({ level }: ConfidenceBadgeProps) {
  return <StatusBadge tone={CONFIDENCE_TONES[level]}>{CONFIDENCE_LABELS[level]}</StatusBadge>;
}
