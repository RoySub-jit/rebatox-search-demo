import Link from "next/link";

export const dynamic = "force-dynamic";
export const revalidate = 0;
export const fetchCache = "force-no-store";

import { PageIntro } from "@/components/page-intro";
import { StatusBadge } from "@/components/status-badge";
import {
  ApiClientError,
  listSavedWorkspaces,
  type SavedWorkspaceListItemResponse,
} from "@/lib/api";
import { appConfig } from "@/lib/config";
import {
  formatPublishedAt,
  getProviderLabel,
  getSearchModeConfig,
} from "@/lib/live-workspace";

function describeLoadError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to load saved workspaces.";
}

function countByEntityType(items: SavedWorkspaceListItemResponse[], entityType: string) {
  return items.filter((item) => item.entity_type === entityType).length;
}

export default async function SavedWorkspacesPage() {
  try {
    const response = await listSavedWorkspaces(appConfig.apiBaseUrl, 24);
    const moleculeCount = countByEntityType(response.items, "molecule");
    const degradantCount = countByEntityType(response.items, "degradant");
    const elCount = countByEntityType(response.items, "el");

    return (
      <div className="page-stack">
        <PageIntro
          eyebrow="Saved review library"
          title="Saved workspaces"
          description="Reopen prior RebaTox snapshots with the same source context, extracted signals, and reviewer-ready framing."
          actions={
            <>
              <StatusBadge tone="success">{response.total_results} saved snapshots</StatusBadge>
              <StatusBadge tone="neutral">Review continuity</StatusBadge>
            </>
          }
        />

        <section className="executive-summary-grid">
          <article className="executive-summary-card">
            <span className="executive-summary-eyebrow">Molecule workspaces</span>
            <strong className="executive-summary-value">{moleculeCount}</strong>
            <p className="executive-summary-copy">
              Label-backed molecule snapshots saved from live retrieval and kept ready
              for reopening.
            </p>
          </article>
          <article className="executive-summary-card">
            <span className="executive-summary-eyebrow">Degradant workspaces</span>
            <strong className="executive-summary-value">{degradantCount}</strong>
            <p className="executive-summary-copy">
              Literature-driven degradant workspaces preserved for follow-up review and
              comparison.
            </p>
          </article>
          <article className="executive-summary-card">
            <span className="executive-summary-eyebrow">E&amp;L workspaces</span>
            <strong className="executive-summary-value">{elCount}</strong>
            <p className="executive-summary-copy">
              Extractables and leachables topics saved with their original evidence
              grounding and search context.
            </p>
          </article>
        </section>

        {response.items.length === 0 ? (
          <section className="card empty-state">
            <div>
              <h2>No saved workspaces yet</h2>
              <p className="empty-copy">
                Save a live search workspace and it will appear here as a reusable review
                snapshot.
              </p>
              <div className="button-row">
                <Link className="button-primary" href="/search">
                  Start from live search
                </Link>
              </div>
            </div>
          </section>
        ) : (
          <section className="saved-workspace-grid">
            {response.items.map((item) => {
              const modeConfig = getSearchModeConfig(item.entity_type);

              return (
                <article key={item.id} className="saved-workspace-card">
                  <div className="saved-workspace-top">
                    <div>
                      <span className="section-kicker">{modeConfig.label} snapshot</span>
                      <h2>{item.label}</h2>
                      {item.record_title !== item.label ? (
                        <p className="saved-workspace-subtitle">{item.record_title}</p>
                      ) : null}
                    </div>
                    <div className="badge-row">
                      <StatusBadge tone="info">{getProviderLabel(item.provider)}</StatusBadge>
                      <StatusBadge tone="neutral">{modeConfig.label}</StatusBadge>
                    </div>
                  </div>

                  <p className="saved-workspace-summary">
                    {item.record_summary ??
                      item.notes ??
                      "Saved live-review snapshot with structured source context and extracted evidence cues."}
                  </p>

                  <div className="search-result-meta">
                    <div className="overview-block">
                      <span className="overview-label">Saved</span>
                      <strong>{formatPublishedAt(item.saved_at)}</strong>
                    </div>
                    <div className="overview-block">
                      <span className="overview-label">Original query</span>
                      <strong>{item.query ?? "Direct record open"}</strong>
                    </div>
                    <div className="overview-block">
                      <span className="overview-label">Signals</span>
                      <strong>{item.extracted_signal_count}</strong>
                    </div>
                    <div className="overview-block">
                      <span className="overview-label">Sections</span>
                      <strong>{item.section_count}</strong>
                    </div>
                  </div>

                  <div className="button-row">
                    <Link className="button-primary" href={`/workspace?saved_id=${item.id}`}>
                      Open saved workspace
                    </Link>
                    {item.query ? (
                      <Link
                        className="button-secondary"
                        href={`/search?entity_type=${item.entity_type}&q=${encodeURIComponent(item.query)}&results=1`}
                      >
                        Revisit live search
                      </Link>
                    ) : null}
                  </div>
                </article>
              );
            })}
          </section>
        )}
      </div>
    );
  } catch (error) {
    return (
      <div className="page-stack">
        <section className="card feedback-banner danger">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Saved review library</span>
              <h2>Saved workspaces unavailable</h2>
            </div>
            <StatusBadge tone="danger">API issue</StatusBadge>
          </div>
          <p>{describeLoadError(error)}</p>
          <div className="button-row">
            <Link className="button-secondary" href="/search">
              Back to live search
            </Link>
          </div>
        </section>
      </div>
    );
  }
}
