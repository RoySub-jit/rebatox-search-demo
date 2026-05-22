export type CalculationType =
  | "mg_per_kg_day_to_mg_per_day"
  | "mg_per_day_to_mg_per_kg_day"
  | "margin_of_exposure"
  | "pde"
  | "ade";

export type ReportCitationResponse = {
  source_document_id: number | null;
  source_document_title: string;
  citation_span_id: number | null;
  label: string | null;
  quoted_text: string | null;
  chunk_index: number | null;
  page_number_start: number | null;
  page_number_end: number | null;
};

export type ComparatorSummaryItemResponse = {
  comparator_id: number;
  name: string;
  category: string | null;
  description: string | null;
  relevance_score: number;
  relevance_rationale: string;
  linked_study_count: number;
  linked_candidate_pod_count: number;
  citations: ReportCitationResponse[];
};

export type EvidenceStudyItemResponse = {
  study_id: number;
  title: string;
  study_design: string | null;
  status: string | null;
  source_document_title: string | null;
  published_at: string | null;
  citations: ReportCitationResponse[];
};

export type EvidenceFindingItemResponse = {
  finding_id: number;
  study_id: number;
  study_title: string;
  title: string;
  summary: string;
  finding_type: string | null;
  evidence_direction: string | null;
  effect_estimate: number | null;
  citations: ReportCitationResponse[];
};

export type CalculationSummaryItemResponse = {
  calculation_id: number;
  calculation_type: string;
  status: string;
  formula_version: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
  assumptions: string[];
  warnings: string[];
  citations: ReportCitationResponse[];
};

export type CandidatePODAssessmentItemResponse = {
  candidate_pod_id: number;
  title: string;
  claim_text: string;
  rationale: string | null;
  status: string;
  confidence_score: number | null;
  support_category: string;
  support_score: number;
  confidence_rationale: string;
  expert_review_required: boolean;
  comparator_name: string | null;
  linked_finding_title: string | null;
  citations: ReportCitationResponse[];
};

export type SupportCategory =
  | "explicit_pod_available"
  | "inferred_pod_from_public_data"
  | "analog_supported_provisional_pod"
  | "insufficient_public_data_for_pod";

export type SearchEntityType = "molecule" | "degradant" | "el";
export type LiveSourceProvider = "dailymed" | "openfda" | "pubmed" | "pubchem" | "echa";

export type LiveSearchResultResponse = {
  entity_type: SearchEntityType;
  provider: LiveSourceProvider;
  external_id: string;
  title: string;
  subtitle: string | null;
  summary: string | null;
  document_type: string | null;
  published_at: string | null;
  source_uri: string | null;
  identifiers: {
    namespace: string;
    value: string;
  }[];
  generic_name: string | null;
  brand_names: string[];
  manufacturer_names: string[];
  routes: string[];
  substance_names: string[];
  product_type: string | null;
  authors: string[];
  journal: string | null;
  keywords: string[];
};

export type LiveSearchResponse = {
  entity_type: SearchEntityType;
  query: string;
  sources: LiveSourceProvider[];
  limit: number;
  total_results: number;
  warnings: string[];
  items: LiveSearchResultResponse[];
};

export type LiveWorkspaceSectionResponse = {
  key: string;
  title: string;
  content: string[];
};

export type LiveWorkspaceExtractedSignalResponse = {
  key: string;
  label: string;
  value: string;
  source_section_key: string | null;
  confidence: "high" | "medium" | "low";
};

export type LiveWorkspaceDoseCandidateResponse = {
  dose_text: string;
  dose_value: number | null;
  unit: string | null;
  normalized_mg_per_kg_day: number | null;
  normalization_note: string | null;
  pod_term: string | null;
  species: string | null;
  route: string | null;
  duration: string | null;
  sentence: string;
  confidence: "high" | "medium" | "low";
};

export type LiveWorkspaceDerivedCalculationResponse = {
  key: string;
  label: string;
  formula: string;
  result_text: string;
  unit: string | null;
  assumptions: string[];
};

export type LiveWorkspacePodAnalysisResponse = {
  primary_candidate: LiveWorkspaceDoseCandidateResponse | null;
  candidates: LiveWorkspaceDoseCandidateResponse[];
  derived_calculations: LiveWorkspaceDerivedCalculationResponse[];
  warnings: string[];
};

export type LiveWorkspacePodWorksheetResponse = {
  selected_candidate_index: number | null;
  body_weight_kg: number;
  uncertainty_factor: number;
  use_human_equivalent_dose: boolean;
  reviewer_status: "draft" | "reviewed" | "accepted" | "rejected";
  reviewer_notes: string | null;
  selected_candidate: LiveWorkspaceDoseCandidateResponse | null;
  selected_basis_label: string | null;
  selected_basis_mg_per_kg_day: number | null;
  hed_basis_mg_per_kg_day: number | null;
  screening_intake_mg_day: number | null;
  uf_adjusted_intake_mg_day: number | null;
  calculations: LiveWorkspaceDerivedCalculationResponse[];
  warnings: string[];
};

export type LiveWorkspaceResponse = {
  entity_type: SearchEntityType;
  query: string | null;
  record: LiveSearchResultResponse;
  sections: LiveWorkspaceSectionResponse[];
  extracted_signals: LiveWorkspaceExtractedSignalResponse[];
  pod_analysis: LiveWorkspacePodAnalysisResponse;
  pod_worksheet: LiveWorkspacePodWorksheetResponse;
  review_cue: {
    title: string;
    description: string;
  };
  retrieval_mode: "live";
  retrieved_at: string;
};

export type SavedWorkspaceResponse = {
  id: number;
  label: string;
  notes: string | null;
  entity_type: SearchEntityType;
  provider: LiveSearchResultResponse["provider"];
  external_id: string;
  query: string | null;
  saved_at: string;
  workspace: LiveWorkspaceResponse;
};

export type SavedWorkspaceListItemResponse = {
  id: number;
  label: string;
  notes: string | null;
  entity_type: SearchEntityType;
  provider: LiveSearchResultResponse["provider"];
  external_id: string;
  query: string | null;
  saved_at: string;
  record_title: string;
  record_summary: string | null;
  extracted_signal_count: number;
  section_count: number;
};

export type SavedWorkspaceListResponse = {
  total_results: number;
  items: SavedWorkspaceListItemResponse[];
};

export type MoleculeSearchResultResponse = {
  provider: "dailymed" | "openfda" | "pubmed";
  external_id: string;
  title: string;
  generic_name: string | null;
  brand_names: string[];
  manufacturer_names: string[];
  routes: string[];
  substance_names: string[];
  product_type: string | null;
  published_at: string | null;
  summary: string | null;
  source_uri: string | null;
  identifiers: {
    namespace: string;
    value: string;
  }[];
};

export type MoleculeSearchResponse = {
  query: string;
  limit: number;
  total_results: number;
  items: MoleculeSearchResultResponse[];
};

export type MoleculeLabelSectionResponse = {
  key: string;
  title: string;
  content: string[];
};

export type MoleculeDetailResponse = {
  molecule: MoleculeSearchResultResponse;
  sections: MoleculeLabelSectionResponse[];
};

export type ReportLimitationItemResponse = {
  source: "persisted" | "generated" | "recommendation";
  title: string;
  description: string;
  severity: string | null;
  why_it_matters: string;
  resolution_suggestion: string;
  is_blocking: boolean;
  study_title: string | null;
  finding_title: string | null;
  candidate_pod_title: string | null;
  citations: ReportCitationResponse[];
};

export type SuggestedExperimentItemResponse = {
  source: "persisted" | "generated" | "recommendation";
  title: string;
  rationale: string;
  priority: string | null;
  linked_limitation_title: string | null;
  recommendation_status: string | null;
  citations: ReportCitationResponse[];
};

export type ExpertReviewItemResponse = {
  expert_review_id: number;
  reviewer_name: string;
  reviewer_email: string | null;
  linked_candidate_pod_id: number | null;
  verdict: string;
  score: number | null;
  accepted_current_assessment: boolean;
  expert_review_required_resolved: boolean;
  override_support_category: SupportCategory | null;
  override_support_score: number | null;
  notes: string | null;
  reviewed_at: string | null;
  linked_finding_title: string | null;
  linked_candidate_pod_title: string | null;
  citations: ReportCitationResponse[];
};

export type ProductReportResponse = {
  product_id: number;
  generated_at: string;
  product_overview: {
    name: string;
    slug: string;
    manufacturer: string | null;
    description: string | null;
    study_count: number;
    finding_count: number;
    candidate_pod_count: number;
    citations: ReportCitationResponse[];
  };
  comparator_summary: {
    items: ComparatorSummaryItemResponse[];
    citations: ReportCitationResponse[];
  };
  evidence_summary: {
    study_count: number;
    finding_count: number;
    studies: EvidenceStudyItemResponse[];
    findings: EvidenceFindingItemResponse[];
    calculations: CalculationSummaryItemResponse[];
    citations: ReportCitationResponse[];
  };
  candidate_pod_assessment: {
    items: CandidatePODAssessmentItemResponse[];
    citations: ReportCitationResponse[];
  };
  limitations: {
    items: ReportLimitationItemResponse[];
    citations: ReportCitationResponse[];
  };
  suggested_next_experiments: {
    items: SuggestedExperimentItemResponse[];
    citations: ReportCitationResponse[];
  };
  expert_review_section: {
    review_count: number;
    average_score: number | null;
    items: ExpertReviewItemResponse[];
    citations: ReportCitationResponse[];
  };
};

export type CalculationOutput = {
  calculator: string;
  formula: string;
  inputs: Record<string, string | number>;
  assumptions: string[];
  result: Record<string, string | number | boolean | null> | null;
  warnings: string[];
  status: "ok" | "warning" | "error";
};

export type CalculationRunResponse = {
  id: number;
  run_type: CalculationType;
  status: "ok" | "warning";
  product_id: number | null;
  comparator_id: number | null;
  study_id: number | null;
  candidate_pod_id: number | null;
  inputs: Record<string, string | number>;
  output: CalculationOutput;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type RunCalculationPayload = {
  run_type: CalculationType;
  inputs: Record<string, string>;
  product_id?: number;
  comparator_id?: number;
  study_id?: number;
  candidate_pod_id?: number;
};

export type ExpertReviewPayload = {
  candidate_pod_id: number;
  calculation_run_id?: number | null;
  reviewer_name: string;
  reviewer_email?: string | null;
  verdict: string;
  score?: number | null;
  accepted_current_assessment: boolean;
  expert_review_required_resolved: boolean;
  override_support_category?: SupportCategory | null;
  override_support_score?: number | null;
  notes?: string | null;
  reviewed_at?: string | null;
};

export type ExpertReviewResponse = {
  id: number;
  candidate_pod_id: number | null;
  finding_id: number | null;
  calculation_run_id: number | null;
  reviewer_name: string;
  reviewer_email: string | null;
  verdict: string;
  score: number | null;
  accepted_current_assessment: boolean;
  expert_review_required_resolved: boolean;
  override_support_category: SupportCategory | null;
  override_support_score: number | null;
  notes: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
};

type ApiErrorPayload = {
  detail?:
    | {
        code?: string;
        message?: string;
      }
    | string;
};

export class ApiClientError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
  }
}

async function requestJson<T>(
  apiBaseUrl: string,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let message = "Request failed.";
    let code: string | undefined;

    try {
      const payload = (await response.json()) as ApiErrorPayload;
      if (typeof payload.detail === "string") {
        message = payload.detail;
      } else if (payload.detail) {
        message = payload.detail.message ?? message;
        code = payload.detail.code;
      }
    } catch {
      message = response.statusText || message;
    }

    throw new ApiClientError(message, response.status, code);
  }

  return (await response.json()) as T;
}

export function runCalculation(
  apiBaseUrl: string,
  payload: RunCalculationPayload,
) {
  return requestJson<CalculationRunResponse>(
    apiBaseUrl,
    "/api/v1/calculations/run",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function getCalculationRun(apiBaseUrl: string, calculationId: number) {
  return requestJson<CalculationRunResponse>(
    apiBaseUrl,
    `/api/v1/calculations/${calculationId}`,
    {
      method: "GET",
    },
  );
}

export function getProductReport(apiBaseUrl: string, productId: number) {
  return requestJson<ProductReportResponse>(
    apiBaseUrl,
    `/api/v1/reports/${productId}`,
    {
      method: "GET",
    },
  );
}

export function createExpertReview(
  apiBaseUrl: string,
  payload: ExpertReviewPayload,
) {
  return requestJson<ExpertReviewResponse>(apiBaseUrl, "/api/v1/expert-reviews", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateExpertReview(
  apiBaseUrl: string,
  expertReviewId: number,
  payload: ExpertReviewPayload,
) {
  return requestJson<ExpertReviewResponse>(
    apiBaseUrl,
    `/api/v1/expert-reviews/${expertReviewId}`,
    {
      method: "PUT",
      body: JSON.stringify(payload),
    },
  );
}

export function searchMolecules(
  apiBaseUrl: string,
  query: string,
  limit = 10,
) {
  const params = new URLSearchParams({
    q: query,
    limit: String(limit),
  });

  return requestJson<MoleculeSearchResponse>(
    apiBaseUrl,
    `/api/v1/molecule-search?${params.toString()}`,
    {
      method: "GET",
    },
  );
}

export function getMoleculeDetail(
  apiBaseUrl: string,
  provider: MoleculeSearchResultResponse["provider"],
  externalId: string,
) {
  return requestJson<MoleculeDetailResponse>(
    apiBaseUrl,
    `/api/v1/molecule-search/${provider}/${encodeURIComponent(externalId)}`,
    {
      method: "GET",
    },
  );
}

export function searchLiveRecords(
  apiBaseUrl: string,
  entityType: SearchEntityType,
  query: string,
  limit = 10,
  sources?: string[],
) {
  const params = new URLSearchParams({
    entity_type: entityType,
    q: query,
    limit: String(limit),
  });

  if (sources && sources.length > 0) {
    params.set("sources", sources.join(","));
  }

  return requestJson<LiveSearchResponse>(
    apiBaseUrl,
    `/api/v1/search?${params.toString()}`,
    {
      method: "GET",
    },
  );
}

export function resolveLiveWorkspace(
  apiBaseUrl: string,
  payload: {
    entity_type: SearchEntityType;
    provider: LiveSearchResultResponse["provider"];
    external_id: string;
    query?: string | null;
  },
) {
  return requestJson<LiveWorkspaceResponse>(apiBaseUrl, "/api/v1/workspaces/resolve", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function saveLiveWorkspace(
  apiBaseUrl: string,
  payload: {
    workspace: LiveWorkspaceResponse;
    label?: string | null;
    notes?: string | null;
  },
) {
  return requestJson<SavedWorkspaceResponse>(apiBaseUrl, "/api/v1/workspaces/save", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateSavedWorkspace(
  apiBaseUrl: string,
  workspaceId: number,
  payload: {
    workspace: LiveWorkspaceResponse;
    label?: string | null;
    notes?: string | null;
  },
) {
  return requestJson<SavedWorkspaceResponse>(
    apiBaseUrl,
    `/api/v1/workspaces/${workspaceId}`,
    {
      method: "PUT",
      body: JSON.stringify(payload),
    },
  );
}

export function getSavedWorkspace(apiBaseUrl: string, workspaceId: number) {
  return requestJson<SavedWorkspaceResponse>(
    apiBaseUrl,
    `/api/v1/workspaces/${workspaceId}`,
    {
      method: "GET",
    },
  );
}

export function listSavedWorkspaces(apiBaseUrl: string, limit = 24) {
  const params = new URLSearchParams({
    limit: String(limit),
  });

  return requestJson<SavedWorkspaceListResponse>(
    apiBaseUrl,
    `/api/v1/workspaces?${params.toString()}`,
    {
      method: "GET",
    },
  );
}
