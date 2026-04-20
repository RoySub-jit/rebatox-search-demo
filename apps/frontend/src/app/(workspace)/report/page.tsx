import { CitationPanel } from "@/components/citation-panel";
import { InfoTable } from "@/components/info-table";
import { PageIntro } from "@/components/page-intro";
import { StatCard } from "@/components/stat-card";
import { StatusBadge } from "@/components/status-badge";
import {
  reportCitations,
  reportMetrics,
  reportRows,
  reportSections,
} from "@/lib/demo-data";

const sectionColumns = [
  { key: "section", label: "Section" },
  { key: "owner", label: "Owner" },
  { key: "status", label: "Status" },
  { key: "lastEdited", label: "Last edited", align: "right" as const },
];

const claimColumns = [
  { key: "claim", label: "Claim" },
  { key: "strength", label: "Support" },
  { key: "source", label: "Primary source" },
  { key: "state", label: "State", align: "right" as const },
];

export default function ReportPage() {
  return (
    <div className="page-stack">
      <PageIntro
        eyebrow="Decision memo"
        title="Report assembly"
        description="Turn the evidence package into a publication-ready report with section-level status, claim strength, and traceable citations."
        actions={<StatusBadge tone="success">Draft 0.8</StatusBadge>}
      />

      <section className="metric-grid">
        {reportMetrics.map((metric) => (
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
              <span className="section-kicker">Authoring progress</span>
              <h2>Section readiness</h2>
            </div>
            <StatusBadge tone="warning">2 sections need updates</StatusBadge>
          </div>
          <InfoTable columns={sectionColumns} rows={reportSections} />
        </article>

        <article className="card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Claim matrix</span>
              <h2>Key narrative statements</h2>
            </div>
            <StatusBadge tone="info">Evidence linked</StatusBadge>
          </div>
          <InfoTable columns={claimColumns} rows={reportRows} />
        </article>
      </section>

      <section className="card">
        <div className="card-heading">
          <div>
            <span className="section-kicker">Traceability</span>
            <h2>Claim-level citation drilldown</h2>
          </div>
          <StatusBadge tone="neutral">Ready for export</StatusBadge>
        </div>
        <div className="citation-stack">
          {reportCitations.map((citation) => (
            <CitationPanel key={citation.id} citation={citation} />
          ))}
        </div>
      </section>
    </div>
  );
}
