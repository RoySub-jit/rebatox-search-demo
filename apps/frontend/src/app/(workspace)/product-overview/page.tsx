import { InfoTable } from "@/components/info-table";
import { PageIntro } from "@/components/page-intro";
import { StatCard } from "@/components/stat-card";
import { StatusBadge } from "@/components/status-badge";
import {
  comparatorRows,
  productHighlights,
  productMetrics,
  productMilestones,
  productSnapshot,
} from "@/lib/demo-data";

const comparatorColumns = [
  { key: "arm", label: "Arm" },
  { key: "evidence", label: "Evidence" },
  { key: "exposure", label: "Exposure band" },
  { key: "readiness", label: "Readiness", align: "right" as const },
];

const milestoneColumns = [
  { key: "phase", label: "Phase" },
  { key: "owner", label: "Owner" },
  { key: "status", label: "Status" },
  { key: "eta", label: "ETA", align: "right" as const },
];

export default function ProductOverviewPage() {
  return (
    <div className="page-stack">
      <PageIntro
        eyebrow="Program cockpit"
        title={productSnapshot.name}
        description={productSnapshot.summary}
        actions={
          <>
            <StatusBadge tone="success">{productSnapshot.stage}</StatusBadge>
            <StatusBadge tone="info">{productSnapshot.regulatoryTrack}</StatusBadge>
          </>
        }
      />

      <section className="metric-grid">
        {productMetrics.map((metric) => (
          <StatCard
            key={metric.label}
            label={metric.label}
            value={metric.value}
            hint={metric.hint}
            tone={metric.tone}
          />
        ))}
      </section>

      <section className="content-grid">
        <article className="card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Program snapshot</span>
              <h2>Why this product is moving now</h2>
            </div>
            <StatusBadge tone="neutral">{productSnapshot.owner}</StatusBadge>
          </div>
          <div className="highlight-list">
            {productHighlights.map((highlight) => (
              <div className="highlight-item" key={highlight.title}>
                <div className="highlight-title-row">
                  <h3>{highlight.title}</h3>
                  <StatusBadge tone={highlight.tone}>{highlight.badge}</StatusBadge>
                </div>
                <p>{highlight.body}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Decision frame</span>
              <h2>Comparator landscape</h2>
            </div>
            <StatusBadge tone="warning">3 active comparators</StatusBadge>
          </div>
          <InfoTable columns={comparatorColumns} rows={comparatorRows} />
        </article>
      </section>

      <section className="card">
        <div className="card-heading">
          <div>
            <span className="section-kicker">Execution timeline</span>
            <h2>Milestones and next gates</h2>
          </div>
          <StatusBadge tone="success">On track</StatusBadge>
        </div>
        <InfoTable columns={milestoneColumns} rows={productMilestones} />
      </section>
    </div>
  );
}
