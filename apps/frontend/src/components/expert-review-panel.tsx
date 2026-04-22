"use client";

import {
  startTransition,
  useEffect,
  useEffectEvent,
  useState,
} from "react";
import { useRouter } from "next/navigation";

import { StatusBadge } from "@/components/status-badge";
import {
  ApiClientError,
  createExpertReview,
  updateExpertReview,
  type CandidatePODAssessmentItemResponse,
  type ExpertReviewItemResponse,
  type ExpertReviewPayload,
  type SupportCategory,
} from "@/lib/api";
import {
  formatDateTime,
  formatNumericScore,
  getSupportCategoryLabel,
  getSupportCategoryTone,
  getVerdictTone,
  hasExpertOverride,
} from "@/lib/report-review";

type ExpertReviewPanelProps = {
  apiBaseUrl: string;
  candidatePod: CandidatePODAssessmentItemResponse;
  reviews: ExpertReviewItemResponse[];
};

type ReviewDraft = {
  reviewerName: string;
  reviewerEmail: string;
  verdict: string;
  score: string;
  acceptedCurrentAssessment: boolean;
  expertReviewRequiredResolved: boolean;
  overrideSupportCategory: SupportCategory | "";
  overrideSupportScore: string;
  notes: string;
};

const VERDICT_OPTIONS = ["approve", "revise", "reject"] as const;
const SUPPORT_CATEGORY_OPTIONS: SupportCategory[] = [
  "explicit_pod_available",
  "inferred_pod_from_public_data",
  "analog_supported_provisional_pod",
  "insufficient_public_data_for_pod",
];

function buildDraft(
  candidatePod: CandidatePODAssessmentItemResponse,
  latestReview: ExpertReviewItemResponse | null,
): ReviewDraft {
  return {
    reviewerName: latestReview?.reviewer_name ?? "",
    reviewerEmail: latestReview?.reviewer_email ?? "",
    verdict: latestReview?.verdict ?? "revise",
    score:
      latestReview?.score !== null && latestReview?.score !== undefined
        ? String(latestReview.score)
        : "",
    acceptedCurrentAssessment:
      latestReview?.accepted_current_assessment ?? false,
    expertReviewRequiredResolved:
      latestReview?.expert_review_required_resolved ??
      !candidatePod.expert_review_required,
    overrideSupportCategory: latestReview?.override_support_category ?? "",
    overrideSupportScore:
      latestReview?.override_support_score !== null &&
      latestReview?.override_support_score !== undefined
        ? String(latestReview.override_support_score)
        : "",
    notes: latestReview?.notes ?? "",
  };
}

function describeApiError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to save the expert review.";
}

export function ExpertReviewPanel({
  apiBaseUrl,
  candidatePod,
  reviews,
}: ExpertReviewPanelProps) {
  const router = useRouter();
  const latestReview = reviews[0] ?? null;
  const [draft, setDraft] = useState<ReviewDraft>(
    buildDraft(candidatePod, latestReview),
  );
  const [requestError, setRequestError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setDraft(buildDraft(candidatePod, latestReview));
    setRequestError(null);
  }, [candidatePod, latestReview]);

  const saveReview = useEffectEvent(async () => {
    if (!draft.reviewerName.trim()) {
      setRequestError("Reviewer name is required before saving.");
      return;
    }

    setIsSubmitting(true);
    setRequestError(null);
    setSuccessMessage(null);

    const payload: ExpertReviewPayload = {
      candidate_pod_id: candidatePod.candidate_pod_id,
      reviewer_name: draft.reviewerName.trim(),
      reviewer_email: draft.reviewerEmail.trim() || null,
      verdict: draft.verdict,
      score: draft.score.trim() ? Number(draft.score) : null,
      accepted_current_assessment: draft.acceptedCurrentAssessment,
      expert_review_required_resolved: draft.expertReviewRequiredResolved,
      override_support_category: draft.acceptedCurrentAssessment
        ? null
        : draft.overrideSupportCategory || null,
      override_support_score:
        draft.acceptedCurrentAssessment || !draft.overrideSupportScore.trim()
          ? null
          : Number(draft.overrideSupportScore),
      notes: draft.notes.trim() || null,
    };

    try {
      if (latestReview) {
        await updateExpertReview(apiBaseUrl, latestReview.expert_review_id, payload);
        setSuccessMessage("Latest expert review updated. Refreshing report view...");
      } else {
        await createExpertReview(apiBaseUrl, payload);
        setSuccessMessage("Expert review saved. Refreshing report view...");
      }
      startTransition(() => {
        router.refresh();
      });
    } catch (error) {
      setRequestError(describeApiError(error));
    } finally {
      setIsSubmitting(false);
    }
  });

  return (
    <section className="task-item expert-review-panel">
      <div className="task-item-top">
        <div>
          <h3>Expert review and override</h3>
          <p className="field-note">
            Save the expert decision that should govern this candidate POD in
            the current RebaTox report.
          </p>
        </div>
        <div className="badge-row">
          <StatusBadge
            tone={getSupportCategoryTone(candidatePod.support_category)}
          >
            {getSupportCategoryLabel(candidatePod.support_category)}
          </StatusBadge>
          <StatusBadge tone={candidatePod.expert_review_required ? "warning" : "success"}>
            {candidatePod.expert_review_required ? "Needs review" : "Resolved"}
          </StatusBadge>
        </div>
      </div>

      <div className="review-history">
        <div className="review-history-header">
          <h4>Prior decisions</h4>
          <StatusBadge tone={reviews.length > 0 ? "info" : "neutral"}>
            {reviews.length} review{reviews.length === 1 ? "" : "s"}
          </StatusBadge>
        </div>
        {reviews.length === 0 ? (
          <p className="field-note">
            No prior expert decisions have been recorded for this candidate POD.
          </p>
        ) : (
          <ul className="review-history-list">
            {reviews.map((review) => (
              <li key={review.expert_review_id} className="review-history-item">
                <div className="review-history-top">
                  <strong>{review.reviewer_name}</strong>
                  <div className="badge-row">
                    <StatusBadge tone={getVerdictTone(review.verdict)}>
                      {review.verdict}
                    </StatusBadge>
                    {review.score !== null ? (
                      <StatusBadge tone="info">
                        Score {formatNumericScore(review.score)}
                      </StatusBadge>
                    ) : null}
                    {hasExpertOverride(review) ? (
                      <StatusBadge tone="warning">Override captured</StatusBadge>
                    ) : null}
                  </div>
                </div>
                <p>{review.notes ?? "No expert notes recorded."}</p>
                <div className="review-history-meta">
                  <span>{formatDateTime(review.reviewed_at)}</span>
                  <span>
                    {review.override_support_category
                      ? `Category override: ${getSupportCategoryLabel(
                          review.override_support_category,
                        )}`
                      : "No category override"}
                  </span>
                  <span>
                    {review.override_support_score !== null
                      ? `Score override: ${formatNumericScore(
                          review.override_support_score,
                        )}`
                      : "No score override"}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="field-grid">
        <div className="field">
          <label className="field-label" htmlFor={`reviewer-name-${candidatePod.candidate_pod_id}`}>
            Reviewer name
          </label>
          <input
            id={`reviewer-name-${candidatePod.candidate_pod_id}`}
            className="input-control"
            value={draft.reviewerName}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                reviewerName: event.target.value,
              }))
            }
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor={`reviewer-email-${candidatePod.candidate_pod_id}`}>
            Reviewer email
          </label>
          <input
            id={`reviewer-email-${candidatePod.candidate_pod_id}`}
            className="input-control"
            value={draft.reviewerEmail}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                reviewerEmail: event.target.value,
              }))
            }
          />
        </div>
      </div>

      <div className="field-grid">
        <div className="field">
          <label className="field-label" htmlFor={`review-verdict-${candidatePod.candidate_pod_id}`}>
            Final decision status
          </label>
          <select
            id={`review-verdict-${candidatePod.candidate_pod_id}`}
            className="input-control"
            value={draft.verdict}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                verdict: event.target.value,
              }))
            }
          >
            {VERDICT_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label className="field-label" htmlFor={`review-score-${candidatePod.candidate_pod_id}`}>
            Expert score
          </label>
          <input
            id={`review-score-${candidatePod.candidate_pod_id}`}
            className="input-control"
            inputMode="decimal"
            placeholder="Optional"
            value={draft.score}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                score: event.target.value,
              }))
            }
          />
        </div>
      </div>

      <div className="checkbox-row">
        <label className="checkbox-card">
          <input
            type="checkbox"
            checked={draft.acceptedCurrentAssessment}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                acceptedCurrentAssessment: event.target.checked,
                overrideSupportCategory: event.target.checked
                  ? ""
                  : current.overrideSupportCategory,
                overrideSupportScore: event.target.checked
                  ? ""
                  : current.overrideSupportScore,
              }))
            }
          />
          <span>Accept the current support assessment</span>
        </label>
        <label className="checkbox-card">
          <input
            type="checkbox"
            checked={draft.expertReviewRequiredResolved}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                expertReviewRequiredResolved: event.target.checked,
              }))
            }
          />
          <span>Mark expert review required as resolved</span>
        </label>
      </div>

      <div className="field-grid">
        <div className="field">
          <label className="field-label" htmlFor={`override-category-${candidatePod.candidate_pod_id}`}>
            Override support category
          </label>
          <select
            id={`override-category-${candidatePod.candidate_pod_id}`}
            className="input-control"
            disabled={draft.acceptedCurrentAssessment}
            value={draft.overrideSupportCategory}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                overrideSupportCategory: event.target.value as SupportCategory | "",
              }))
            }
          >
            <option value="">Keep current category</option>
            {SUPPORT_CATEGORY_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {getSupportCategoryLabel(option)}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label className="field-label" htmlFor={`override-score-${candidatePod.candidate_pod_id}`}>
            Override support score
          </label>
          <input
            id={`override-score-${candidatePod.candidate_pod_id}`}
            className="input-control"
            inputMode="decimal"
            disabled={draft.acceptedCurrentAssessment}
            placeholder="0-100"
            value={draft.overrideSupportScore}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                overrideSupportScore: event.target.value,
              }))
            }
          />
        </div>
      </div>

      <div className="field">
        <label className="field-label" htmlFor={`review-notes-${candidatePod.candidate_pod_id}`}>
          Expert notes
        </label>
        <textarea
          id={`review-notes-${candidatePod.candidate_pod_id}`}
          className="input-control textarea-control"
          rows={4}
          value={draft.notes}
          onChange={(event) =>
            setDraft((current) => ({
              ...current,
              notes: event.target.value,
            }))
          }
        />
      </div>

      <div className="button-row">
        <button
          className="button-primary"
          disabled={isSubmitting}
          onClick={() => void saveReview()}
          type="button"
        >
          {isSubmitting
            ? "Saving expert review..."
            : latestReview
              ? "Update latest review"
              : "Save expert review"}
        </button>
      </div>

      {requestError ? (
        <div className="feedback-banner danger">
          <strong>Expert review error</strong>
          <p>{requestError}</p>
        </div>
      ) : null}
      {successMessage ? (
        <div className="feedback-banner success">
          <strong>Expert review saved</strong>
          <p>{successMessage}</p>
        </div>
      ) : null}
    </section>
  );
}
