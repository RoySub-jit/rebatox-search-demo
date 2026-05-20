"use client";

import { useState } from "react";
import Link from "next/link";

import {
  ApiClientError,
  saveLiveWorkspace,
  type LiveWorkspaceResponse,
  type SavedWorkspaceResponse,
} from "@/lib/api";

type WorkspaceSavePanelProps = {
  apiBaseUrl: string;
  workspace: LiveWorkspaceResponse;
};

function describeSaveError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to save this workspace right now.";
}

export function WorkspaceSavePanel({
  apiBaseUrl,
  workspace,
}: WorkspaceSavePanelProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [savedWorkspace, setSavedWorkspace] = useState<SavedWorkspaceResponse | null>(
    null,
  );

  async function handleSave() {
    if (isSaving || savedWorkspace) {
      return;
    }

    setIsSaving(true);
    setSaveError(null);

    try {
      const response = await saveLiveWorkspace(apiBaseUrl, {
        workspace,
      });
      setSavedWorkspace(response);
    } catch (error) {
      setSaveError(describeSaveError(error));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="card">
      <div className="card-heading">
        <div>
          <h2>Save this workspace</h2>
          <p className="empty-copy">
            Persist the current live snapshot so you can reopen the same reviewed
            evidence later.
          </p>
        </div>
      </div>

      {savedWorkspace ? (
        <div className="feedback-banner success">
          <p>
            Saved as workspace #{savedWorkspace.id}. You can reopen the saved snapshot
            any time.
          </p>
          <div className="button-row">
            <Link
              className="button-primary"
              href={`/workspace?saved_id=${savedWorkspace.id}`}
            >
              Open saved workspace
            </Link>
            <Link className="button-secondary" href="/saved-workspaces">
              View saved workspaces
            </Link>
          </div>
        </div>
      ) : (
        <>
          <div className="button-row">
            <button
              className="button-primary"
              type="button"
              onClick={handleSave}
              disabled={isSaving}
            >
              {isSaving ? "Saving..." : "Save workspace snapshot"}
            </button>
          </div>
          {saveError ? (
            <div className="feedback-banner danger">
              <p>{saveError}</p>
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}
