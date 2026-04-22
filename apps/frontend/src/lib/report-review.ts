import type {
  ExpertReviewItemResponse,
  ProductReportResponse,
  ReportCitationResponse,
} from "@/lib/api";

export type ReviewTone =
  | "neutral"
  | "success"
  | "warning"
  | "danger"
  | "info";

export type ReviewMetric = {
  label: string;
  value: string;
  hint: string;
  tone: ReviewTone;
};

export type SparseReportState = {
  comparators: boolean;
  calculations: boolean;
  candidatePods: boolean;
  limitations: boolean;
  suggestedExperiments: boolean;
  expertReviews: boolean;
};

export type CitationPanelModel = {
  id: string;
  title: string;
  source: string;
  excerpt: string;
  interpretation: string;
  pages: string;
  label: string;
  tone: ReviewTone;
  entityLabel?: string;
  fieldLabel?: string;
};

export type CandidatePodReviewState = {
  latestReview: ExpertReviewItemResponse | null;
  history: ExpertReviewItemResponse[];
  overrideApplied: boolean;
  reviewResolved: boolean;
};

type CitationPanelOptions = {
  itemKey: string;
  itemTitle: string;
  badgeLabel: string;
  interpretation: string;
  tone?: ReviewTone;
  entityLabel?: string;
  fieldLabel?: string;
};

const SUPPORT_CATEGORY_LABELS: Record<string, string> = {
  explicit_pod_available: "Explicit POD available",
  inferred_pod_from_public_data: "Inferred from public data",
  analog_supported_provisional_pod: "Analog-supported provisional POD",
  insufficient_public_data_for_pod: "Insufficient public data",
};

export function formatNumericScore(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "—";
  }

  return value.toFixed(1);
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "Not recorded";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function getSupportCategoryLabel(category: string): string {
  return SUPPORT_CATEGORY_LABELS[category] ?? category.replaceAll("_", " ");
}

export function getSupportCategoryTone(category: string): ReviewTone {
  switch (category) {
    case "explicit_pod_available":
      return "success";
    case "inferred_pod_from_public_data":
      return "info";
    case "analog_supported_provisional_pod":
      return "warning";
    case "insufficient_public_data_for_pod":
      return "danger";
    default:
      return "neutral";
  }
}

export function getReviewRequiredTone(required: boolean): ReviewTone {
  return required ? "warning" : "success";
}

export function getComparatorTone(score: number): ReviewTone {
  if (score >= 80) {
    return "success";
  }
  if (score >= 40) {
    return "info";
  }
  return "warning";
}

export function getLimitationSeverityTone(severity: string | null): ReviewTone {
  switch ((severity ?? "").toLowerCase()) {
    case "high":
      return "danger";
    case "medium":
      return "warning";
    case "low":
      return "info";
    default:
      return "neutral";
  }
}

export function getCalculationStatusTone(status: string): ReviewTone {
  switch (status) {
    case "ok":
      return "success";
    case "warning":
      return "warning";
    case "error":
      return "danger";
    default:
      return "neutral";
  }
}

export function getPriorityTone(priority: string | null): ReviewTone {
  switch ((priority ?? "").toLowerCase()) {
    case "high":
      return "danger";
    case "medium":
      return "warning";
    case "low":
      return "info";
    default:
      return "neutral";
  }
}

export function getVerdictTone(verdict: string): ReviewTone {
  switch (verdict.toLowerCase()) {
    case "approve":
      return "success";
    case "revise":
      return "warning";
    case "reject":
      return "danger";
    default:
      return "neutral";
  }
}

export function getSparseReportState(
  report: ProductReportResponse,
): SparseReportState {
  return {
    comparators: report.comparator_summary.items.length === 0,
    calculations: report.evidence_summary.calculations.length === 0,
    candidatePods: report.candidate_pod_assessment.items.length === 0,
    limitations: report.limitations.items.length === 0,
    suggestedExperiments: report.suggested_next_experiments.items.length === 0,
    expertReviews: report.expert_review_section.items.length === 0,
  };
}

export function buildReviewMetrics(
  report: ProductReportResponse,
): ReviewMetric[] {
  const reviewRequiredCount = report.candidate_pod_assessment.items.filter(
    (item) => item.expert_review_required,
  ).length;
  const blockingLimitationCount = report.limitations.items.filter(
    (item) => item.is_blocking,
  ).length;

  return [
    {
      label: "Comparators",
      value: String(report.comparator_summary.items.length),
      hint: "Comparator relevance carried into the reviewer workspace.",
      tone: report.comparator_summary.items.length > 0 ? "success" : "neutral",
    },
    {
      label: "Calculation audits",
      value: String(report.evidence_summary.calculations.length),
      hint: "Deterministic run summaries linked to the evidence package.",
      tone:
        report.evidence_summary.calculations.length > 0 ? "info" : "neutral",
    },
    {
      label: "Expert review required",
      value: String(reviewRequiredCount),
      hint: "Candidate PODs still flagged for explicit expert confirmation.",
      tone: reviewRequiredCount > 0 ? "warning" : "success",
    },
    {
      label: "Blocking limitations",
      value: String(blockingLimitationCount),
      hint: "High-severity issues that still block a clean tox story.",
      tone: blockingLimitationCount > 0 ? "danger" : "success",
    },
  ];
}

export function getExpertReviewHistoryForCandidatePod(
  reviews: ExpertReviewItemResponse[],
  candidatePodId: number,
): ExpertReviewItemResponse[] {
  return reviews.filter(
    (review) => review.linked_candidate_pod_id === candidatePodId,
  );
}

export function hasExpertOverride(review: ExpertReviewItemResponse | null): boolean {
  if (!review) {
    return false;
  }

  return (
    review.override_support_category !== null ||
    review.override_support_score !== null ||
    review.accepted_current_assessment ||
    review.expert_review_required_resolved
  );
}

export function getCandidatePodReviewState(
  report: ProductReportResponse,
  candidatePodId: number,
): CandidatePodReviewState {
  const history = getExpertReviewHistoryForCandidatePod(
    report.expert_review_section.items,
    candidatePodId,
  );
  const latestReview = history[0] ?? null;

  return {
    latestReview,
    history,
    overrideApplied: hasExpertOverride(latestReview),
    reviewResolved: latestReview?.expert_review_required_resolved ?? false,
  };
}

export function formatPageRange(citation: ReportCitationResponse): string {
  if (
    citation.page_number_start === null ||
    citation.page_number_start === undefined
  ) {
    return "Page metadata unavailable";
  }

  if (
    citation.page_number_end === null ||
    citation.page_number_end === undefined ||
    citation.page_number_end === citation.page_number_start
  ) {
    return `Page ${citation.page_number_start}`;
  }

  return `Pages ${citation.page_number_start}-${citation.page_number_end}`;
}

export function buildCitationPanelModels(
  citations: ReportCitationResponse[],
  options: CitationPanelOptions,
): CitationPanelModel[] {
  return citations.map((citation, index) => ({
    id: `${options.itemKey}-${citation.citation_span_id ?? index}`,
    title: `${options.itemTitle} citation ${index + 1}`,
    source: citation.source_document_title,
    excerpt:
      citation.quoted_text ??
      "No direct excerpt was stored for this item, but the source document still grounds the review record.",
    interpretation: options.interpretation,
    pages: formatPageRange(citation),
    label: options.badgeLabel,
    tone: options.tone ?? "info",
    entityLabel: options.entityLabel,
    fieldLabel: options.fieldLabel ?? citation.label ?? undefined,
  }));
}
