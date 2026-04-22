const { test } = require("node:test");
const assert = require("node:assert/strict");

const {
  buildCitationPanelModels,
  buildReviewMetrics,
  getCandidatePodReviewState,
  getSparseReportState,
  getSupportCategoryLabel,
  getSupportCategoryTone,
} = require("./report-review.ts");

function buildPopulatedReport() {
  return {
    product_id: 7,
    generated_at: "2026-04-21T18:00:00Z",
    product_overview: {
      name: "Cardiovex XR",
      slug: "cardiovex-xr",
      manufacturer: "Example Labs",
      description: "Extended-release safety assessment candidate.",
      study_count: 1,
      finding_count: 1,
      candidate_pod_count: 1,
      citations: [],
    },
    comparator_summary: {
      items: [
        {
          comparator_id: 1,
          name: "Reference Alpha",
          category: "active_control",
          description: "Strong comparator bridge",
          relevance_score: 100,
          relevance_rationale: "Reference Alpha is a strong comparator match.",
          linked_study_count: 1,
          linked_candidate_pod_count: 1,
          citations: [],
        },
      ],
      citations: [],
    },
    evidence_summary: {
      study_count: 1,
      finding_count: 1,
      studies: [],
      findings: [],
      calculations: [
        {
          calculation_id: 3,
          calculation_type: "margin_of_exposure",
          status: "ok",
          formula_version: "1.0",
          inputs: { point_of_departure: "100", exposure: "2" },
          outputs: { value: "50.0", unit: "ratio" },
          assumptions: ["Same basis used for POD and exposure."],
          warnings: [],
          citations: [
            {
              source_document_id: 11,
              source_document_title: "CSR CVX-301",
              citation_span_id: 5,
              label: "calculation_support",
              quoted_text: "Systemic exposure remained within the maintenance band.",
              chunk_index: 0,
              page_number_start: 21,
              page_number_end: 22,
            },
          ],
        },
      ],
      citations: [],
    },
    candidate_pod_assessment: {
      items: [
        {
          candidate_pod_id: 9,
          title: "Lead NOAEL candidate",
          claim_text: "NOAEL of 5 mg/kg/day retained.",
          rationale: "Direct product evidence and comparator support align.",
          status: "confirmed",
          confidence_score: 0.93,
          support_category: "explicit_pod_available",
          support_score: 99.16,
          confidence_rationale: "Explicit POD wording is present.",
          expert_review_required: false,
          comparator_name: "Reference Alpha",
          linked_finding_title: "Reference alignment",
          citations: [],
        },
      ],
      citations: [],
    },
    limitations: {
      items: [],
      citations: [],
    },
    suggested_next_experiments: {
      items: [],
      citations: [],
    },
    expert_review_section: {
      review_count: 1,
      average_score: 4,
      items: [
        {
          expert_review_id: 1,
          reviewer_name: "Dr. Ada Review",
          reviewer_email: "ada@example.test",
          linked_candidate_pod_id: 9,
          verdict: "approve",
          score: 4,
          accepted_current_assessment: true,
          expert_review_required_resolved: true,
          override_support_category: null,
          override_support_score: null,
          notes: "Ready for finalization.",
          reviewed_at: "2026-04-20T09:00:00Z",
          linked_finding_title: "Reference alignment",
          linked_candidate_pod_title: "Lead NOAEL candidate",
          citations: [],
        },
      ],
      citations: [],
    },
  };
}

function buildSparseReport() {
  return {
    product_id: 8,
    generated_at: "2026-04-21T18:00:00Z",
    product_overview: {
      name: "Sparse Candidate",
      slug: "sparse-candidate",
      manufacturer: null,
      description: null,
      study_count: 0,
      finding_count: 0,
      candidate_pod_count: 0,
      citations: [],
    },
    comparator_summary: { items: [], citations: [] },
    evidence_summary: {
      study_count: 0,
      finding_count: 0,
      studies: [],
      findings: [],
      calculations: [],
      citations: [],
    },
    candidate_pod_assessment: { items: [], citations: [] },
    limitations: { items: [], citations: [] },
    suggested_next_experiments: { items: [], citations: [] },
    expert_review_section: {
      review_count: 0,
      average_score: null,
      items: [],
      citations: [],
    },
  };
}

test("report-review helpers summarize a populated report", () => {
  const report = buildPopulatedReport();

  const metrics = buildReviewMetrics(report);
  const sparse = getSparseReportState(report);

  assert.deepEqual(
    metrics.map((item) => item.value),
    ["1", "1", "0", "0"],
  );
  assert.equal(metrics[0].tone, "success");
  assert.equal(metrics[1].tone, "info");
  assert.equal(metrics[2].tone, "success");
  assert.deepEqual(sparse, {
    comparators: false,
    calculations: false,
    candidatePods: false,
    limitations: true,
    suggestedExperiments: true,
    expertReviews: false,
  });
  assert.equal(
    getSupportCategoryLabel(report.candidate_pod_assessment.items[0].support_category),
    "Explicit POD available",
  );
  assert.equal(
    getSupportCategoryTone(report.candidate_pod_assessment.items[0].support_category),
    "success",
  );
});

test("report-review helpers flag sparse report empty states", () => {
  const report = buildSparseReport();

  assert.deepEqual(getSparseReportState(report), {
    comparators: true,
    calculations: true,
    candidatePods: true,
    limitations: true,
    suggestedExperiments: true,
    expertReviews: true,
  });

  const metrics = buildReviewMetrics(report);
  assert.deepEqual(
    metrics.map((item) => item.value),
    ["0", "0", "0", "0"],
  );
});

test("report-review helpers build expandable citation panel models", () => {
  const report = buildPopulatedReport();
  const citationModels = buildCitationPanelModels(
    report.evidence_summary.calculations[0].citations,
    {
      itemKey: "calc-3",
      itemTitle: "Margin of exposure",
      badgeLabel: "Calculation audit",
      interpretation:
        "This citation grounds the calculation audit trail in the reviewer workspace.",
      entityLabel: "Margin of exposure",
      fieldLabel: "Calculation support",
      tone: "info",
    },
  );

  assert.equal(citationModels.length, 1);
  assert.equal(citationModels[0].title, "Margin of exposure citation 1");
  assert.equal(citationModels[0].source, "CSR CVX-301");
  assert.equal(citationModels[0].pages, "Pages 21-22");
  assert.equal(citationModels[0].label, "Calculation audit");
  assert.equal(citationModels[0].entityLabel, "Margin of exposure");
  assert.equal(
    citationModels[0].interpretation,
    "This citation grounds the calculation audit trail in the reviewer workspace.",
  );
});

test("report-review helpers surface prior expert notes and override state", () => {
  const report = buildPopulatedReport();
  report.expert_review_section.items.unshift({
    expert_review_id: 2,
    reviewer_name: "Dr. Override Review",
    reviewer_email: "override@example.test",
    linked_candidate_pod_id: 9,
    verdict: "revise",
    score: 3.8,
    accepted_current_assessment: false,
    expert_review_required_resolved: true,
    override_support_category: "inferred_pod_from_public_data",
    override_support_score: 67,
    notes: "Use the inferred category until the bridge package is finalized.",
    reviewed_at: "2026-04-21T10:00:00Z",
    linked_finding_title: "Reference alignment",
    linked_candidate_pod_title: "Lead NOAEL candidate",
    citations: [],
  });

  const reviewState = getCandidatePodReviewState(report, 9);

  assert.equal(reviewState.history.length, 2);
  assert.equal(reviewState.latestReview?.reviewer_name, "Dr. Override Review");
  assert.equal(reviewState.latestReview?.notes, "Use the inferred category until the bridge package is finalized.");
  assert.equal(reviewState.overrideApplied, true);
  assert.equal(reviewState.reviewResolved, true);
});
