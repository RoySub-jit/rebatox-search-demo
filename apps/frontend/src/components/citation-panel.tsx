import { ConfidenceBadge, type ConfidenceLevel } from "@/components/confidence-badge";
import { SourceTypeBadge, type SourceType } from "@/components/source-type-badge";
import { StatusBadge, type BadgeTone } from "@/components/status-badge";

export type CitationRecord = {
  id: string;
  title: string;
  source: string;
  excerpt: string;
  interpretation: string;
  pages: string;
  label: string;
  tone: BadgeTone;
  sourceType?: SourceType;
  confidence?: ConfidenceLevel;
  fieldLabel?: string;
  entityLabel?: string;
};

type CitationPanelProps = {
  citation: CitationRecord;
};

export function CitationPanel({ citation }: CitationPanelProps) {
  return (
    <details className="citation-panel">
      <summary className="citation-summary">
        <div className="citation-summary-copy">
          <span className="citation-source">{citation.source}</span>
          <h3>{citation.title}</h3>
          <p>{citation.pages}</p>
          {citation.entityLabel || citation.sourceType || citation.confidence || citation.fieldLabel ? (
            <div className="citation-meta-row">
              {citation.entityLabel ? (
                <span className="citation-chip">{citation.entityLabel}</span>
              ) : null}
              {citation.fieldLabel ? (
                <span className="citation-chip">{citation.fieldLabel}</span>
              ) : null}
              {citation.sourceType ? (
                <SourceTypeBadge sourceType={citation.sourceType} />
              ) : null}
              {citation.confidence ? (
                <ConfidenceBadge level={citation.confidence} />
              ) : null}
            </div>
          ) : null}
        </div>
        <StatusBadge tone={citation.tone}>{citation.label}</StatusBadge>
      </summary>
      <div className="citation-body">
        <blockquote>{citation.excerpt}</blockquote>
        <p>{citation.interpretation}</p>
      </div>
    </details>
  );
}
