import { CitationPanel } from "@/components/citation-panel";
import { ConfidenceBadge } from "@/components/confidence-badge";
import { InfoTable } from "@/components/info-table";
import { PageIntro } from "@/components/page-intro";
import { SourceTypeBadge } from "@/components/source-type-badge";
import { StatCard } from "@/components/stat-card";
import { StatusBadge } from "@/components/status-badge";
import {
  evidenceCitations,
  extractedStudyDetails,
  evidenceMetrics,
  findingRows,
  candidatePodRows,
  sourceDocumentRows,
} from "@/lib/evidence-data";

const sourceDocumentColumns = [
  { key: "document", label: "Document" },
  { key: "sourceType", label: "Source type" },
  { key: "coverage", label: "Coverage" },
  { key: "confidence", label: "Confidence" },
  { key: "status", label: "State", align: "right" as const },
];

const findingColumns = [
  { key: "finding", label: "Finding" },
  { key: "supportingStudy", label: "Supporting evidence" },
  { key: "confidence", label: "Confidence" },
  { key: "status", label: "Status", align: "right" as const },
];

const candidatePodColumns = [
  { key: "candidate", label: "Candidate POD" },
  { key: "basis", label: "Evidence basis" },
  { key: "caveat", label: "Caveat" },
  { key: "confidence", label: "Confidence" },
  { key: "status", label: "State", align: "right" as const },
];

export default function EvidencePage() {
  return (
    <div className="page-stack">
      <PageIntro
        eyebrow="Evidence map"
        title="Sources, extraction, findings, and POD traceability"
        description="Inspect the evidence chain end to end: source documents, structured study-detail extraction, findings, candidate PODs, and citation-level drill-down in one professional review surface."
        actions={
          <>
            <SourceTypeBadge sourceType="clinical" />
            <ConfidenceBadge level="high" />
            <StatusBadge tone="info">27 extracted fields mapped</StatusBadge>
          </>
        }
      />

      <section className="metric-grid">
        {evidenceMetrics.map((metric) => (
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
              <span className="section-kicker">Source inventory</span>
              <h2>Source documents</h2>
            </div>
            <StatusBadge tone="success">4 source lanes active</StatusBadge>
          </div>
          <InfoTable columns={sourceDocumentColumns} rows={sourceDocumentRows} />
        </article>

        <article className="card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Hybrid extraction</span>
              <h2>Extracted study details</h2>
            </div>
            <StatusBadge tone="info">Rule-based first</StatusBadge>
          </div>
          <div className="study-card-stack">
            {extractedStudyDetails.map((study) => (
              <article className="study-card" key={study.id}>
                <div className="study-card-head">
                  <div className="study-card-copy">
                    <h3>{study.title}</h3>
                    <p>{study.summary}</p>
                    <span className="study-card-source">{study.sourceDocument}</span>
                  </div>
                  <div className="badge-row">
                    <SourceTypeBadge sourceType={study.sourceType} />
                    <ConfidenceBadge level={study.confidence} />
                    <StatusBadge tone="neutral">{study.coverageLabel}</StatusBadge>
                  </div>
                </div>
                <div className="study-field-grid">
                  {study.fields.map((field) => (
                    <div className="study-field" key={`${study.id}-${field.label}`}>
                      <span className="study-field-label">{field.label}</span>
                      <div className="study-field-value">{field.value}</div>
                      <p className="study-field-note">{field.citation}</p>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="content-grid">
        <article className="card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Evidence synthesis</span>
              <h2>Findings</h2>
            </div>
            <StatusBadge tone="success">3 findings linked</StatusBadge>
          </div>
          <InfoTable columns={findingColumns} rows={findingRows} />
        </article>

        <article className="card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Quantitative framing</span>
              <h2>Candidate PODs</h2>
            </div>
            <StatusBadge tone="warning">1 caveat still open</StatusBadge>
          </div>
          <InfoTable columns={candidatePodColumns} rows={candidatePodRows} />
        </article>
      </section>

      <section className="card">
        <div className="card-heading">
          <div>
            <span className="section-kicker">Citation drill-down</span>
            <h2>Trace each extracted field and evidence claim</h2>
          </div>
          <StatusBadge tone="info">Expandable span review</StatusBadge>
        </div>
        <div className="citation-stack">
          {evidenceCitations.map((citation) => (
            <CitationPanel key={citation.id} citation={citation} />
          ))}
        </div>
      </section>
    </div>
  );
}
