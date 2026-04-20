export type SourceType =
  | "clinical"
  | "nonclinical"
  | "literature"
  | "regulatory"
  | "review";

const SOURCE_TYPE_LABELS: Record<SourceType, string> = {
  clinical: "Clinical",
  nonclinical: "Nonclinical",
  literature: "Literature",
  regulatory: "Regulatory",
  review: "Review packet",
};

type SourceTypeBadgeProps = {
  sourceType: SourceType;
};

export function SourceTypeBadge({ sourceType }: SourceTypeBadgeProps) {
  return (
    <span className={`badge source-type-badge source-type-${sourceType}`}>
      {SOURCE_TYPE_LABELS[sourceType]}
    </span>
  );
}
