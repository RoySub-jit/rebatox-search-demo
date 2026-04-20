import { StatusBadge, type BadgeTone } from "@/components/status-badge";

type StatCardProps = {
  label: string;
  value: string;
  hint: string;
  tone: BadgeTone;
};

export function StatCard({ label, value, hint, tone }: StatCardProps) {
  return (
    <article className="metric-card">
      <div className="metric-card-top">
        <span className="metric-label">{label}</span>
        <StatusBadge tone={tone}>{tone}</StatusBadge>
      </div>
      <div className="metric-value">{value}</div>
      <p className="metric-hint">{hint}</p>
    </article>
  );
}
