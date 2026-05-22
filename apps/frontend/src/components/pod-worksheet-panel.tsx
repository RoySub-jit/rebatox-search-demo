"use client";

import { startTransition, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { StatusBadge } from "@/components/status-badge";
import {
  ApiClientError,
  saveLiveWorkspace,
  updateSavedWorkspace,
  type LiveWorkspaceResponse,
  type SavedWorkspaceResponse,
} from "@/lib/api";

type PodWorksheetPanelProps = {
  apiBaseUrl: string;
  workspace: LiveWorkspaceResponse;
  savedWorkspace: SavedWorkspaceResponse | null;
};

type WorksheetDraft = {
  label: string;
  notes: string;
  selectedCandidateIndex: string;
  bodyWeightKg: string;
  uncertaintyFactor: string;
  useHumanEquivalentDose: boolean;
  reviewerStatus: "draft" | "reviewed" | "accepted" | "rejected";
  reviewerNotes: string;
};

const REVIEWER_STATUS_OPTIONS = [
  { value: "draft", label: "Draft" },
  { value: "reviewed", label: "Reviewed" },
  { value: "accepted", label: "Accepted" },
  { value: "rejected", label: "Rejected" },
] as const;

function buildDraft(
  workspace: LiveWorkspaceResponse,
  savedWorkspace: SavedWorkspaceResponse | null,
): WorksheetDraft {
  return {
    label: savedWorkspace?.label ?? workspace.record.title,
    notes: savedWorkspace?.notes ?? "",
    selectedCandidateIndex:
      workspace.pod_worksheet.selected_candidate_index !== null
        ? String(workspace.pod_worksheet.selected_candidate_index)
        : "",
    bodyWeightKg: String(workspace.pod_worksheet.body_weight_kg ?? 50),
    uncertaintyFactor: String(workspace.pod_worksheet.uncertainty_factor ?? 100),
    useHumanEquivalentDose: workspace.pod_worksheet.use_human_equivalent_dose,
    reviewerStatus: workspace.pod_worksheet.reviewer_status,
    reviewerNotes: workspace.pod_worksheet.reviewer_notes ?? "",
  };
}

function describeRequestError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unable to persist the POD worksheet right now.";
}

function getStatusTone(status: WorksheetDraft["reviewerStatus"]) {
  switch (status) {
    case "accepted":
      return "success" as const;
    case "rejected":
      return "danger" as const;
    case "reviewed":
      return "info" as const;
    default:
      return "warning" as const;
  }
}

export function PodWorksheetPanel({
  apiBaseUrl,
  workspace,
  savedWorkspace,
}: PodWorksheetPanelProps) {
  const router = useRouter();
  const [draft, setDraft] = useState<WorksheetDraft>(
    buildDraft(workspace, savedWorkspace),
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    setDraft(buildDraft(workspace, savedWorkspace));
    setRequestError(null);
  }, [workspace, savedWorkspace]);

  const candidateOptions = workspace.pod_analysis.candidates;

  const canUseHumanEquivalentDose = useMemo(() => {
    return candidateOptions.some(
      (candidate) =>
        candidate.species !== null && candidate.species !== "human",
    );
  }, [candidateOptions]);

  async function handlePersistWorksheet() {
    if (isSubmitting) {
      return;
    }

    const bodyWeightKg = Number(draft.bodyWeightKg);
    const uncertaintyFactor = Number(draft.uncertaintyFactor);
    const selectedCandidateIndex =
      draft.selectedCandidateIndex.trim() === ""
        ? null
        : Number(draft.selectedCandidateIndex);

    if (!Number.isFinite(bodyWeightKg) || bodyWeightKg <= 0) {
      setRequestError("Body weight must be a positive number before saving the worksheet.");
      return;
    }

    if (!Number.isFinite(uncertaintyFactor) || uncertaintyFactor < 1) {
      setRequestError(
        "Composite uncertainty factor must be at least 1 before saving the worksheet.",
      );
      return;
    }

    if (
      selectedCandidateIndex !== null &&
      (!Number.isInteger(selectedCandidateIndex) || selectedCandidateIndex < 0)
    ) {
      setRequestError("Selected POD candidate is not valid for this worksheet.");
      return;
    }

    setIsSubmitting(true);
    setRequestError(null);
    setSuccessMessage(null);

    try {
      const updatedWorkspace: LiveWorkspaceResponse = {
        ...workspace,
        pod_worksheet: {
          ...workspace.pod_worksheet,
          selected_candidate_index: selectedCandidateIndex,
          body_weight_kg: bodyWeightKg,
          uncertainty_factor: uncertaintyFactor,
          use_human_equivalent_dose:
            canUseHumanEquivalentDose && draft.useHumanEquivalentDose,
          reviewer_status: draft.reviewerStatus,
          reviewer_notes: draft.reviewerNotes.trim() || null,
        },
      };

      if (savedWorkspace) {
        const response = await updateSavedWorkspace(apiBaseUrl, savedWorkspace.id, {
          workspace: updatedWorkspace,
          label: draft.label.trim() || workspace.record.title,
          notes: draft.notes.trim() || null,
        });
        setSuccessMessage("Saved workspace worksheet updated. Refreshing the reviewer view...");
        startTransition(() => {
          router.replace(`/workspace?saved_id=${response.id}`);
          router.refresh();
        });
        return;
      }

      const response = await saveLiveWorkspace(apiBaseUrl, {
        workspace: updatedWorkspace,
        label: draft.label.trim() || workspace.record.title,
        notes: draft.notes.trim() || null,
      });
      setSuccessMessage("Workspace snapshot saved with the current POD worksheet. Opening the saved version...");
      startTransition(() => {
        router.replace(`/workspace?saved_id=${response.id}`);
        router.refresh();
      });
    } catch (error) {
      setRequestError(describeRequestError(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="card">
      <div className="card-heading">
        <div>
          <h2>Reviewer POD worksheet</h2>
          <p className="empty-copy">
            Adjust the screening assumptions, choose the strongest POD candidate,
            and persist a curated worksheet state for later stewardship review.
          </p>
        </div>
        <div className="badge-row">
          <StatusBadge tone={getStatusTone(draft.reviewerStatus)}>
            {draft.reviewerStatus}
          </StatusBadge>
          <StatusBadge
            tone={savedWorkspace ? "success" : "info"}
          >
            {savedWorkspace ? `Saved #${savedWorkspace.id}` : "Unsaved live worksheet"}
          </StatusBadge>
        </div>
      </div>

      <div className="field-grid">
        <div className="field">
          <label className="field-label" htmlFor="worksheet-label">
            Workspace label
          </label>
          <input
            id="worksheet-label"
            className="input-control"
            value={draft.label}
            onChange={(event) =>
              setDraft((current) => ({ ...current, label: event.target.value }))
            }
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor="worksheet-status">
            Reviewer status
          </label>
          <select
            id="worksheet-status"
            className="input-control"
            value={draft.reviewerStatus}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                reviewerStatus: event.target.value as WorksheetDraft["reviewerStatus"],
              }))
            }
          >
            {REVIEWER_STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="field-grid">
        <div className="field">
          <label className="field-label" htmlFor="worksheet-candidate">
            Selected POD candidate
          </label>
          <select
            id="worksheet-candidate"
            className="input-control"
            value={draft.selectedCandidateIndex}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                selectedCandidateIndex: event.target.value,
              }))
            }
            disabled={candidateOptions.length === 0}
          >
            {candidateOptions.length === 0 ? (
              <option value="">No ranked candidates available</option>
            ) : null}
            {candidateOptions.map((candidate, index) => (
              <option key={`${candidate.dose_text}-${index}`} value={String(index)}>
                {(candidate.pod_term ?? "Dose cue") + " - " + candidate.dose_text}
              </option>
            ))}
          </select>
          <p className="field-note">
            RebaTox will recompute the worksheet using the selected ranked candidate.
          </p>
        </div>
        <div className="field">
          <label className="field-label" htmlFor="worksheet-notes">
            Snapshot notes
          </label>
          <textarea
            id="worksheet-notes"
            className="input-control textarea-control"
            value={draft.notes}
            onChange={(event) =>
              setDraft((current) => ({ ...current, notes: event.target.value }))
            }
          />
        </div>
      </div>

      <div className="field-grid">
        <div className="field">
          <label className="field-label" htmlFor="worksheet-body-weight">
            Body weight (kg)
          </label>
          <input
            id="worksheet-body-weight"
            className="input-control"
            type="number"
            min="1"
            step="0.1"
            value={draft.bodyWeightKg}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                bodyWeightKg: event.target.value,
              }))
            }
          />
        </div>
        <div className="field">
          <label className="field-label" htmlFor="worksheet-uf">
            Composite uncertainty factor
          </label>
          <input
            id="worksheet-uf"
            className="input-control"
            type="number"
            min="1"
            step="1"
            value={draft.uncertaintyFactor}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                uncertaintyFactor: event.target.value,
              }))
            }
          />
        </div>
      </div>

      <div className="checkbox-row">
        <label className="checkbox-card" htmlFor="worksheet-hed">
          <input
            id="worksheet-hed"
            type="checkbox"
            checked={draft.useHumanEquivalentDose && canUseHumanEquivalentDose}
            disabled={!canUseHumanEquivalentDose}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                useHumanEquivalentDose: event.target.checked,
              }))
            }
          />
          <span>
            Use a screening human equivalent dose basis when the selected candidate is
            non-human.
          </span>
        </label>
      </div>

      <div className="field">
        <label className="field-label" htmlFor="worksheet-reviewer-notes">
          Reviewer notes
        </label>
        <textarea
          id="worksheet-reviewer-notes"
          className="input-control textarea-control"
          value={draft.reviewerNotes}
          onChange={(event) =>
            setDraft((current) => ({
              ...current,
              reviewerNotes: event.target.value,
            }))
          }
        />
      </div>

      <div className="button-row">
        <button
          className="button-primary"
          type="button"
          onClick={handlePersistWorksheet}
          disabled={isSubmitting}
        >
          {isSubmitting
            ? savedWorkspace
              ? "Updating worksheet..."
              : "Saving worksheet..."
            : savedWorkspace
              ? "Update saved worksheet"
              : "Save worksheet snapshot"}
        </button>
        {savedWorkspace ? (
          <Link className="button-secondary" href="/saved-workspaces">
            View saved workspaces
          </Link>
        ) : null}
      </div>

      {successMessage ? (
        <div className="feedback-banner success">
          <p>{successMessage}</p>
        </div>
      ) : null}

      {requestError ? (
        <div className="feedback-banner danger">
          <p>{requestError}</p>
        </div>
      ) : null}
    </section>
  );
}
