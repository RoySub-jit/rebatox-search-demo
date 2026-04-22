import type { ReactNode } from "react";

import { CitationPanel } from "@/components/citation-panel";
import { PageIntro } from "@/components/page-intro";
import { StatCard } from "@/components/stat-card";
import { StatusBadge } from "@/components/status-badge";
import type {
  CalculationSummaryItemResponse,
  CandidatePODAssessmentItemResponse,
  ComparatorSummaryItemResponse,
  ExpertReviewItemResponse,
  ProductReportResponse,
  ReportCitationResponse,
  ReportLimitationItemResponse,
  SuggestedExperimentItemResponse,
} from "@/lib/api";
import {
  buildCitationPanelModels,
  buildReviewMetrics,
  formatDateTime,
  formatNumericScore,
  getCalculationStatusTone,
  getComparatorTone,
  getLimitationSeverityTone,
  getPriorityTone,
  getReviewRequiredTone,
  getSparseReportState,
  getSupportCategoryLabel,
  getSupportCategoryTone,
  getVerdictTone,
} from "@/lib/report-review";

type ReportReviewWorkspaceProps = {
  productId: number;
  report: ProductReportResponse;
};

type DetailRowProps = {
  title: string;
  subtitle?: string | null;
  badges?: ReactNode;
  meta?: ReactNode;
  children: ReactNode;
};

type EmptySectionStateProps = {
  title: string;
  copy: string;
};

function DetailRow({
  title,
  subtitle,
  badges,
  meta,
  children,
}: DetailRowProps) {
  return (
    <details className="review-row">
      <summary className="review-row-summary">
        <div className="review-row-copy">
          <h3>{title}</h3>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        <div className="review-row-aside">
          {badges ? <div className="badge-row">{badges}</div> : null}
          {meta ? <div className="review-row-meta">{meta}</div> : null}
        </div>
      </summary>
      <div className="review-row-body">{children}</div>
    </details>
  );
}

function EmptySectionState({ title, copy }: EmptySectionStateProps) {
  return (
    <div className="empty-state review-empty-state">
      <div className="empty-copy">
        <h3>{title}</h3>
        <p>{copy}</p>
      </div>
    </div>
  );
}

function ItemCitations({
  citations,
  itemKey,
  itemTitle,
  badgeLabel,
  interpretation,
  entityLabel,
  fieldLabel,
  tone,
}: {
  citations: ReportCitationResponse[];
  itemKey: string;
  itemTitle: string;
  badgeLabel: string;
  interpretation: string;
  entityLabel?: string;
  fieldLabel?: string;
  tone?: Parameters<typeof buildCitationPanelModels>[1]["tone"];
}) {
  if (citations.length === 0) {
    return null;
  }

  const panels = buildCitationPanelModels(citations, {
    itemKey,
    itemTitle,
    badgeLabel,
    interpretation,
    entityLabel,
    fieldLabel,
    tone,
  });

  return (
    <div className="citation-stack review-citation-stack">
      {panels.map((citation) => (
        <CitationPanel key={citation.id} citation={citation} />
      ))}
    </div>
  );
}

function ComparatorList({
  items,
}: {
  items: ComparatorSummaryItemResponse[];
}) {
  if (items.length === 0) {
    return (
      <EmptySectionState
        title="No comparators linked"
        copy="This report does not yet include a comparator bridge, so the reviewer workspace stays focused on direct product evidence."
      />
    );
  }

  return (
    <div className="review-section-stack">
      {items.map((item) => (
        <DetailRow
          key={item.comparator_id}
          title={item.name}
          subtitle={item.description ?? item.category ?? "Comparator summary available."}
          badges={
            <>
              <StatusBadge tone={getComparatorTone(item.relevance_score)}>
                Relevance {formatNumericScore(item.relevance_score)}
              </StatusBadge>
              <StatusBadge tone="neutral">
                {item.linked_study_count} study link
                {item.linked_study_count === 1 ? "" : "s"}
              </StatusBadge>
            </>
          }
          meta={
            <>
              <span>{item.category ?? "No category"}</span>
              <span>{item.linked_candidate_pod_count} POD link(s)</span>
            </>
          }
        >
          <div className="review-body-grid">
            <article className="highlight-item">
              <div className="highlight-title-row">
                <h3>Relevance rationale</h3>
                <StatusBadge tone={getComparatorTone(item.relevance_score)}>
                  {formatNumericScore(item.relevance_score)} / 100
                </StatusBadge>
              </div>
              <p>{item.relevance_rationale}</p>
            </article>
          </div>
          <ItemCitations
            citations={item.citations}
            itemKey={`comparator-${item.comparator_id}`}
            itemTitle={item.name}
            badgeLabel="Comparator evidence"
            interpretation="These citations ground the comparator relevance summary used in report review."
            entityLabel={item.name}
            tone="info"
          />
        </DetailRow>
      ))}
    </div>
  );
}

function EvidenceSection({ report }: { report: ProductReportResponse }) {
  const { studies, findings, calculations } = report.evidence_summary;

  return (
    <div className="review-section-stack">
      <section className="subsection">
        <div className="card-heading review-subheading">
          <div>
            <span className="section-kicker">Studies</span>
            <h2>Source studies</h2>
          </div>
          <StatusBadge tone={studies.length > 0 ? "success" : "neutral"}>
            {studies.length} {studies.length === 1 ? "study" : "studies"}
          </StatusBadge>
        </div>
        {studies.length === 0 ? (
          <EmptySectionState
            title="No studies available"
            copy="This report has no linked study records yet, so reviewers do not have a primary evidence narrative to inspect."
          />
        ) : (
          <div className="review-section-stack">
            {studies.map((study) => (
              <DetailRow
                key={study.study_id}
                title={study.title}
                subtitle={study.study_design ?? "Study design not recorded."}
                badges={
                  <StatusBadge tone={study.status === "complete" ? "success" : "info"}>
                    {study.status ?? "Unknown status"}
                  </StatusBadge>
                }
                meta={
                  <>
                    <span>{study.source_document_title ?? "No source document"}</span>
                    <span>{formatDateTime(study.published_at)}</span>
                  </>
                }
              >
                <ItemCitations
                  citations={study.citations}
                  itemKey={`study-${study.study_id}`}
                  itemTitle={study.title}
                  badgeLabel="Study evidence"
                  interpretation="These citations ground the study summary in the reviewer workspace."
                  entityLabel={study.title}
                  tone="info"
                />
              </DetailRow>
            ))}
          </div>
        )}
      </section>

      <section className="subsection">
        <div className="card-heading review-subheading">
          <div>
            <span className="section-kicker">Findings</span>
            <h2>Evidence findings</h2>
          </div>
          <StatusBadge tone={findings.length > 0 ? "info" : "neutral"}>
            {findings.length} finding{findings.length === 1 ? "" : "s"}
          </StatusBadge>
        </div>
        {findings.length === 0 ? (
          <EmptySectionState
            title="No findings synthesized"
            copy="No evidence findings have been assembled from the current source package."
          />
        ) : (
          <div className="review-section-stack">
            {findings.map((finding) => (
              <DetailRow
                key={finding.finding_id}
                title={finding.title}
                subtitle={finding.summary}
                badges={
                  <>
                    <StatusBadge tone="info">
                      {finding.finding_type ?? "Finding"}
                    </StatusBadge>
                    <StatusBadge tone="neutral">
                      {finding.evidence_direction ?? "Direction not set"}
                    </StatusBadge>
                  </>
                }
                meta={
                  <>
                    <span>{finding.study_title}</span>
                    <span>
                      Effect estimate {formatNumericScore(finding.effect_estimate)}
                    </span>
                  </>
                }
              >
                <ItemCitations
                  citations={finding.citations}
                  itemKey={`finding-${finding.finding_id}`}
                  itemTitle={finding.title}
                  badgeLabel="Finding evidence"
                  interpretation="These citations anchor the finding summary used in review."
                  entityLabel={finding.title}
                  tone="info"
                />
              </DetailRow>
            ))}
          </div>
        )}
      </section>

      <section className="subsection">
        <div className="card-heading review-subheading">
          <div>
            <span className="section-kicker">Calculation audit</span>
            <h2>Deterministic calculation trails</h2>
          </div>
          <StatusBadge tone={calculations.length > 0 ? "warning" : "neutral"}>
            {calculations.length} audit trail{calculations.length === 1 ? "" : "s"}
          </StatusBadge>
        </div>
        {calculations.length === 0 ? (
          <EmptySectionState
            title="No calculation runs linked"
            copy="The current report does not have any saved deterministic calculations attached to its evidence package."
          />
        ) : (
          <div className="review-section-stack">
            {calculations.map((calculation) => (
              <CalculationAuditRow
                key={calculation.calculation_id}
                calculation={calculation}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function CalculationAuditRow({
  calculation,
}: {
  calculation: CalculationSummaryItemResponse;
}) {
  return (
    <DetailRow
      title={calculation.calculation_type.replaceAll("_", " ")}
      subtitle={`Formula version ${calculation.formula_version}`}
      badges={
        <>
          <StatusBadge tone={getCalculationStatusTone(calculation.status)}>
            {calculation.status}
          </StatusBadge>
          {calculation.warnings.length > 0 ? (
            <StatusBadge tone="warning">
              {calculation.warnings.length} warning
              {calculation.warnings.length === 1 ? "" : "s"}
            </StatusBadge>
          ) : null}
        </>
      }
      meta={
        <>
          <span>Calculation #{calculation.calculation_id}</span>
          <span>{Object.keys(calculation.inputs).length} input field(s)</span>
        </>
      }
    >
      <div className="audit-grid">
        <article className="highlight-item">
          <div className="highlight-title-row">
            <h3>Inputs</h3>
            <StatusBadge tone="neutral">Structured</StatusBadge>
          </div>
          <pre className="code-panel">
            {JSON.stringify(calculation.inputs, null, 2)}
          </pre>
        </article>
        <article className="highlight-item">
          <div className="highlight-title-row">
            <h3>Outputs</h3>
            <StatusBadge tone={getCalculationStatusTone(calculation.status)}>
              {calculation.status}
            </StatusBadge>
          </div>
          <pre className="code-panel">
            {JSON.stringify(calculation.outputs, null, 2)}
          </pre>
        </article>
      </div>

      <div className="audit-grid">
        <article className="task-item">
          <div className="task-item-top">
            <h3>Assumptions</h3>
            <StatusBadge tone="info">
              {calculation.assumptions.length} assumption
              {calculation.assumptions.length === 1 ? "" : "s"}
            </StatusBadge>
          </div>
          {calculation.assumptions.length > 0 ? (
            <ul className="bullet-list">
              {calculation.assumptions.map((assumption) => (
                <li key={assumption}>{assumption}</li>
              ))}
            </ul>
          ) : (
            <p>No explicit assumptions were stored for this run.</p>
          )}
        </article>
        <article className="task-item">
          <div className="task-item-top">
            <h3>Warnings</h3>
            <StatusBadge tone={calculation.warnings.length > 0 ? "warning" : "success"}>
              {calculation.warnings.length > 0 ? "Present" : "None"}
            </StatusBadge>
          </div>
          {calculation.warnings.length > 0 ? (
            <ul className="bullet-list">
              {calculation.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          ) : (
            <p>This calculation run completed without structured warnings.</p>
          )}
        </article>
      </div>

      <ItemCitations
        citations={calculation.citations}
        itemKey={`calculation-${calculation.calculation_id}`}
        itemTitle={calculation.calculation_type.replaceAll("_", " ")}
        badgeLabel="Calculation audit"
        interpretation="These citations ground the saved deterministic calculation in the evidence package."
        entityLabel={calculation.calculation_type.replaceAll("_", " ")}
        fieldLabel="Calculation support"
        tone="info"
      />
    </DetailRow>
  );
}

function CandidatePODList({
  items,
}: {
  items: CandidatePODAssessmentItemResponse[];
}) {
  if (items.length === 0) {
    return (
      <EmptySectionState
        title="No candidate PODs assessed"
        copy="No candidate POD records are available for reviewer scoring yet."
      />
    );
  }

  return (
    <div className="review-section-stack">
      {items.map((item) => (
        <DetailRow
          key={item.candidate_pod_id}
          title={item.title}
          subtitle={item.claim_text}
          badges={
            <>
              <StatusBadge tone={getSupportCategoryTone(item.support_category)}>
                {getSupportCategoryLabel(item.support_category)}
              </StatusBadge>
              <StatusBadge tone={getReviewRequiredTone(item.expert_review_required)}>
                {item.expert_review_required
                  ? "Expert review required"
                  : "Reviewer-ready"}
              </StatusBadge>
            </>
          }
          meta={
            <>
              <span>Support score {formatNumericScore(item.support_score)}</span>
              <span>{item.comparator_name ?? "No comparator linked"}</span>
            </>
          }
        >
          <div className="review-body-grid">
            <article className="highlight-item">
              <div className="highlight-title-row">
                <h3>Support rationale</h3>
                <StatusBadge tone={getSupportCategoryTone(item.support_category)}>
                  {formatNumericScore(item.support_score)} / 100
                </StatusBadge>
              </div>
              <p>{item.confidence_rationale}</p>
            </article>
            <article className="task-item">
              <div className="task-item-top">
                <h3>Assessment details</h3>
                <StatusBadge tone="neutral">{item.status}</StatusBadge>
              </div>
              <ul className="bullet-list">
                <li>
                  Confidence score: {formatNumericScore(item.confidence_score)}
                </li>
                <li>
                  Linked finding: {item.linked_finding_title ?? "Not linked"}
                </li>
                <li>Comparator: {item.comparator_name ?? "Not linked"}</li>
              </ul>
              {item.rationale ? <p>{item.rationale}</p> : null}
            </article>
          </div>
          <ItemCitations
            citations={item.citations}
            itemKey={`pod-${item.candidate_pod_id}`}
            itemTitle={item.title}
            badgeLabel="Candidate POD support"
            interpretation="These citations ground the candidate POD assessment used in the report reviewer workspace."
            entityLabel={item.title}
            tone="info"
          />
        </DetailRow>
      ))}
    </div>
  );
}

function LimitationList({ items }: { items: ReportLimitationItemResponse[] }) {
  if (items.length === 0) {
    return (
      <EmptySectionState
        title="No limitations recorded"
        copy="The current report does not surface any persisted or generated limitations."
      />
    );
  }

  return (
    <div className="review-section-stack">
      {items.map((item, index) => (
        <DetailRow
          key={`${item.title}-${index}`}
          title={item.title}
          subtitle={item.description}
          badges={
            <>
              <StatusBadge tone={getLimitationSeverityTone(item.severity)}>
                {item.severity ?? "Severity not set"}
              </StatusBadge>
              {item.is_blocking ? (
                <StatusBadge tone="danger">Blocking</StatusBadge>
              ) : null}
            </>
          }
          meta={
            <>
              <span>{item.study_title ?? "No study linked"}</span>
              <span>{item.finding_title ?? "No finding linked"}</span>
            </>
          }
        >
          <div className="review-body-grid">
            <article className="task-item">
              <div className="task-item-top">
                <h3>Why it matters</h3>
                <StatusBadge tone={getLimitationSeverityTone(item.severity)}>
                  {item.source}
                </StatusBadge>
              </div>
              <p>{item.why_it_matters}</p>
            </article>
            <article className="task-item">
              <div className="task-item-top">
                <h3>Resolution suggestion</h3>
                <StatusBadge tone="info">Action</StatusBadge>
              </div>
              <p>{item.resolution_suggestion}</p>
            </article>
          </div>
          <ItemCitations
            citations={item.citations}
            itemKey={`limitation-${index}`}
            itemTitle={item.title}
            badgeLabel="Limitation evidence"
            interpretation="These citations ground the limitation shown to reviewers."
            entityLabel={item.candidate_pod_title ?? item.study_title ?? item.title}
            tone="warning"
          />
        </DetailRow>
      ))}
    </div>
  );
}

function RecommendationList({
  items,
}: {
  items: SuggestedExperimentItemResponse[];
}) {
  if (items.length === 0) {
    return (
      <EmptySectionState
        title="No suggested next experiments"
        copy="No follow-up experiments or recommendations are currently attached to this report."
      />
    );
  }

  return (
    <div className="review-section-stack">
      {items.map((item, index) => (
        <DetailRow
          key={`${item.title}-${index}`}
          title={item.title}
          subtitle={item.rationale}
          badges={
            <>
              <StatusBadge tone={getPriorityTone(item.priority)}>
                {item.priority ?? "Priority not set"}
              </StatusBadge>
              {item.recommendation_status ? (
                <StatusBadge tone="neutral">{item.recommendation_status}</StatusBadge>
              ) : null}
            </>
          }
          meta={
            <>
              <span>{item.source}</span>
              <span>{item.linked_limitation_title ?? "No linked limitation"}</span>
            </>
          }
        >
          <ItemCitations
            citations={item.citations}
            itemKey={`recommendation-${index}`}
            itemTitle={item.title}
            badgeLabel="Recommendation evidence"
            interpretation="These citations ground the suggested next experiment shown to reviewers."
            entityLabel={item.title}
            tone="info"
          />
        </DetailRow>
      ))}
    </div>
  );
}

function ExpertReviewList({
  items,
}: {
  items: ExpertReviewItemResponse[];
}) {
  if (items.length === 0) {
    return (
      <EmptySectionState
        title="No expert reviews logged"
        copy="No expert review decisions have been linked to this report yet."
      />
    );
  }

  return (
    <div className="review-section-stack">
      {items.map((item) => (
        <DetailRow
          key={item.expert_review_id}
          title={item.reviewer_name}
          subtitle={item.notes ?? "No reviewer notes recorded."}
          badges={
            <>
              <StatusBadge tone={getVerdictTone(item.verdict)}>
                {item.verdict}
              </StatusBadge>
              {item.score !== null ? (
                <StatusBadge tone="info">
                  Score {formatNumericScore(item.score)}
                </StatusBadge>
              ) : null}
            </>
          }
          meta={
            <>
              <span>{item.linked_candidate_pod_title ?? "No candidate POD linked"}</span>
              <span>{formatDateTime(item.reviewed_at)}</span>
            </>
          }
        >
          <div className="review-body-grid">
            <article className="task-item">
              <div className="task-item-top">
                <h3>Reviewer notes</h3>
                <StatusBadge tone={getVerdictTone(item.verdict)}>
                  {item.reviewer_email ?? "No email"}
                </StatusBadge>
              </div>
              <p>{item.notes ?? "No reviewer notes recorded."}</p>
            </article>
            <article className="task-item">
              <div className="task-item-top">
                <h3>Linked record</h3>
                <StatusBadge tone="neutral">Traceability</StatusBadge>
              </div>
              <ul className="bullet-list">
                <li>
                  Candidate POD: {item.linked_candidate_pod_title ?? "Not linked"}
                </li>
                <li>Finding: {item.linked_finding_title ?? "Not linked"}</li>
              </ul>
            </article>
          </div>
          <ItemCitations
            citations={item.citations}
            itemKey={`review-${item.expert_review_id}`}
            itemTitle={item.reviewer_name}
            badgeLabel="Review evidence"
            interpretation="These citations ground the expert review packet shown in the workspace."
            entityLabel={item.linked_candidate_pod_title ?? item.reviewer_name}
            tone="info"
          />
        </DetailRow>
      ))}
    </div>
  );
}

export function ReportReviewWorkspace({
  productId,
  report,
}: ReportReviewWorkspaceProps) {
  const sparse = getSparseReportState(report);
  const metrics = buildReviewMetrics(report);
  const isSparseWorkspace = Object.values(sparse).some(Boolean);

  return (
    <div className="page-stack">
      <PageIntro
        eyebrow="RebaTox reviewer workspace"
        title={`${report.product_overview.name} review in RebaTox`}
        description="Evidence, POD, and Risk Support for Nonclinical Safety. Review the full report package in one place: product context, comparator relevance, evidence and calculations, candidate POD support, limitations, follow-up experiments, and expert review outcomes."
        actions={
          <>
            <StatusBadge tone="neutral">Product #{productId}</StatusBadge>
            <StatusBadge tone={isSparseWorkspace ? "warning" : "success"}>
              {isSparseWorkspace ? "Sparse report" : "Populated report"}
            </StatusBadge>
            <StatusBadge tone="info">
              Generated {formatDateTime(report.generated_at)}
            </StatusBadge>
          </>
        }
      />

      <section className="metric-grid">
        {metrics.map((metric) => (
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
              <span className="section-kicker">Product overview</span>
              <h2>Program framing</h2>
            </div>
            <StatusBadge tone="neutral">{report.product_overview.slug}</StatusBadge>
          </div>
          <div className="review-overview-grid">
            <div className="overview-block">
              <span className="overview-label">Manufacturer</span>
              <strong>{report.product_overview.manufacturer ?? "Not recorded"}</strong>
            </div>
            <div className="overview-block">
              <span className="overview-label">Studies</span>
              <strong>{report.product_overview.study_count}</strong>
            </div>
            <div className="overview-block">
              <span className="overview-label">Findings</span>
              <strong>{report.product_overview.finding_count}</strong>
            </div>
            <div className="overview-block">
              <span className="overview-label">Candidate PODs</span>
              <strong>{report.product_overview.candidate_pod_count}</strong>
            </div>
          </div>
          <p className="overview-copy">
            {report.product_overview.description ??
              "No product-level description has been added to this report yet."}
          </p>
          <ItemCitations
            citations={report.product_overview.citations}
            itemKey={`product-${report.product_id}`}
            itemTitle={report.product_overview.name}
            badgeLabel="Product grounding"
            interpretation="These citations ground the top-level product overview used by reviewers."
            entityLabel={report.product_overview.name}
            tone="info"
          />
        </article>

        <article className="card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Comparator summary</span>
              <h2>Relevance and bridge logic</h2>
            </div>
            <StatusBadge tone={sparse.comparators ? "neutral" : "info"}>
              {report.comparator_summary.items.length} comparator
              {report.comparator_summary.items.length === 1 ? "" : "s"}
            </StatusBadge>
          </div>
          <ComparatorList items={report.comparator_summary.items} />
        </article>
      </section>

      <section className="card">
        <div className="card-heading">
          <div>
            <span className="section-kicker">Evidence summary</span>
            <h2>Studies, findings, and calculation audits</h2>
          </div>
          <StatusBadge tone={sparse.calculations ? "warning" : "info"}>
            {report.evidence_summary.study_count} study /{" "}
            {report.evidence_summary.finding_count} finding /{" "}
            {report.evidence_summary.calculations.length} calculation
          </StatusBadge>
        </div>
        <EvidenceSection report={report} />
      </section>

      <section className="content-grid">
        <article className="card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Candidate POD assessment</span>
              <h2>Support categories and reviewer flags</h2>
            </div>
            <StatusBadge tone={sparse.candidatePods ? "neutral" : "warning"}>
              {report.candidate_pod_assessment.items.filter(
                (item) => item.expert_review_required,
              ).length}{" "}
              review flag(s)
            </StatusBadge>
          </div>
          <CandidatePODList items={report.candidate_pod_assessment.items} />
        </article>

        <article className="card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Limitations</span>
              <h2>Open evidence gaps</h2>
            </div>
            <StatusBadge tone={sparse.limitations ? "neutral" : "danger"}>
              {report.limitations.items.filter((item) => item.is_blocking).length}{" "}
              blocking
            </StatusBadge>
          </div>
          <LimitationList items={report.limitations.items} />
        </article>
      </section>

      <section className="content-grid">
        <article className="card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Suggested next experiments</span>
              <h2>Follow-up actions</h2>
            </div>
            <StatusBadge tone={sparse.suggestedExperiments ? "neutral" : "info"}>
              {report.suggested_next_experiments.items.length} recommendation
              {report.suggested_next_experiments.items.length === 1 ? "" : "s"}
            </StatusBadge>
          </div>
          <RecommendationList items={report.suggested_next_experiments.items} />
        </article>

        <article className="card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Expert review</span>
              <h2>Reviewer decisions and notes</h2>
            </div>
            <StatusBadge tone={sparse.expertReviews ? "neutral" : "success"}>
              Average score {formatNumericScore(report.expert_review_section.average_score)}
            </StatusBadge>
          </div>
          <ExpertReviewList items={report.expert_review_section.items} />
        </article>
      </section>
    </div>
  );
}
