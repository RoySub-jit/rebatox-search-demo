import Link from "next/link";

import { PageIntro } from "@/components/page-intro";
import { StatusBadge } from "@/components/status-badge";
import { WorkspaceSavePanel } from "@/components/workspace-save-panel";
import {
  ApiClientError,
  getSavedWorkspace,
  resolveLiveWorkspace,
  type LiveSearchResultResponse,
  type LiveWorkspaceResponse,
  type SavedWorkspaceResponse,
} from "@/lib/api";
import { appConfig } from "@/lib/config";
import {
  buildWorkspaceOverviewRows,
  formatPublishedAt,
  getProviderLabel,
  getSearchModeConfig,
  isSearchEntityType,
} from "@/lib/live-workspace";

type WorkspacePageProps = {
  searchParams?: Promise<{
    entity_type?: string | string[];
    provider?: string | string[];
    id?: string | string[];
    q?: string | string[];
    saved_id?: string | string[];
  }>;
};

function getSingleValue(input: string | string[] | undefined): string {
  const value = Array.isArray(input) ? input[0] : input;
  return (value ?? "").trim();
}

function describeLoadError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to load the live workspace.";
}

function isSupportedProvider(
  provider: string,
): provider is LiveSearchResultResponse["provider"] {
  return provider === "openfda" || provider === "dailymed" || provider === "pubmed";
}

function buildBackToSearchHref(entityType: string, query: string | null): string {
  return query
    ? `/search?entity_type=${entityType}&q=${encodeURIComponent(query)}&results=1`
    : `/search?entity_type=${entityType}&results=1`;
}

export default async function WorkspacePage({ searchParams }: WorkspacePageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const savedWorkspaceId = getSingleValue(resolvedSearchParams.saved_id);
  const rawEntityType = getSingleValue(resolvedSearchParams.entity_type) || "molecule";
  const provider = getSingleValue(resolvedSearchParams.provider);
  const externalId = getSingleValue(resolvedSearchParams.id);
  const query = getSingleValue(resolvedSearchParams.q);
  const hasSavedWorkspaceSelection = savedWorkspaceId.length > 0;

  if (
    !hasSavedWorkspaceSelection &&
    (!isSearchEntityType(rawEntityType) ||
      !provider ||
      !externalId ||
      !isSupportedProvider(provider))
  ) {
    return (
      <div className="page-stack">
        <section className="card feedback-banner danger">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Live workspace</span>
              <h2>Missing source selection</h2>
            </div>
            <StatusBadge tone="danger">Input error</StatusBadge>
          </div>
          <p>
            Open this page from live search so RebaTox knows which source record to
            resolve into a workspace.
          </p>
          <div className="button-row">
            <Link className="button-secondary search-example-link" href="/search">
              Back to search
            </Link>
          </div>
        </section>
      </div>
    );
  }

  const resolvedEntityType = isSearchEntityType(rawEntityType)
    ? rawEntityType
    : "molecule";
  const resolvedProvider = isSupportedProvider(provider) ? provider : "openfda";

  try {
    let workspace: LiveWorkspaceResponse;
    let savedWorkspace: SavedWorkspaceResponse | null = null;
    let entityType = resolvedEntityType;
    let activeQuery = query || null;

    if (hasSavedWorkspaceSelection) {
      const numericId = Number(savedWorkspaceId);
      if (!Number.isInteger(numericId) || numericId <= 0) {
        throw new ApiClientError("Saved workspace id must be a positive integer.", 400);
      }

      savedWorkspace = await getSavedWorkspace(appConfig.apiBaseUrl, numericId);
      workspace = savedWorkspace.workspace;
      entityType = savedWorkspace.entity_type;
      activeQuery = savedWorkspace.query;
    } else {
      workspace = await resolveLiveWorkspace(appConfig.apiBaseUrl, {
        entity_type: resolvedEntityType,
        provider: resolvedProvider,
        external_id: externalId,
        query: query || null,
      });
      activeQuery = workspace.query;
    }

    const modeConfig = getSearchModeConfig(entityType as LiveWorkspaceResponse["entity_type"]);
    const overviewRows = buildWorkspaceOverviewRows(workspace);
    const backToSearchHref = buildBackToSearchHref(entityType, activeQuery);
    const workspaceStateLabel = savedWorkspace ? "Saved reviewer snapshot" : "Live source workspace";

    return (
      <div className="page-stack">
        <PageIntro
          eyebrow={
            savedWorkspace
              ? `Saved ${modeConfig.label.toLowerCase()} workspace`
              : `Live ${modeConfig.label.toLowerCase()} workspace`
          }
          title={workspace.record.title}
          description={
            workspace.record.summary ??
            "Live source-backed workspace assembled from the current RebaTox query."
          }
          actions={
            <>
              <StatusBadge tone={savedWorkspace ? "success" : "info"}>
                {savedWorkspace ? "Saved snapshot" : "Live retrieval"}
              </StatusBadge>
              <StatusBadge tone="info">
                {getProviderLabel(workspace.record.provider)}
              </StatusBadge>
              <StatusBadge tone="neutral">
                {workspace.record.document_type ??
                  workspace.record.product_type ??
                  "Source record"}
              </StatusBadge>
            </>
          }
        />

        <section className="card workspace-command-bar">
          <div className="workspace-command-copy">
            <span className="section-kicker">Workspace controls</span>
            <h2>Open, save, and trace the current evidence record</h2>
            <p className="empty-copy">
              This workspace keeps the live source view structured for stewardship review
              while preserving an easy path back to alternative matches or the original
              source.
            </p>
          </div>
          <div className="workspace-command-actions">
            <div className="button-row">
              <Link className="button-secondary search-example-link" href={backToSearchHref}>
                Back to search
              </Link>
              {workspace.record.source_uri && workspace.record.provider !== "openfda" ? (
                <a
                  className="button-primary"
                  href={workspace.record.source_uri}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open source record
                </a>
              ) : null}
            </div>
          </div>
        </section>

        <section className="workspace-spotlight-grid">
          <article className="overview-block spotlight-block">
            <span className="overview-label">Workspace state</span>
            <strong>{workspaceStateLabel}</strong>
            <p className="spotlight-copy">
              {savedWorkspace
                ? "Persisted for later reopening with the same reviewed source context."
                : "Resolved directly from the strongest current live public-source match."}
            </p>
          </article>
          <article className="overview-block spotlight-block">
            <span className="overview-label">Source family</span>
            <strong>{getProviderLabel(workspace.record.provider)}</strong>
            <p className="spotlight-copy">
              {workspace.record.document_type ??
                workspace.record.product_type ??
                "Structured source record"}
            </p>
          </article>
          <article className="overview-block spotlight-block">
            <span className="overview-label">Search origin</span>
            <strong>{activeQuery ?? "Direct record open"}</strong>
            <p className="spotlight-copy">
              Retrieved {formatPublishedAt(workspace.retrieved_at)} for the current
              RebaTox review pass.
            </p>
          </article>
        </section>

        <section className="card">
          <div className="card-heading">
            <div>
              <h2>{modeConfig.label} overview</h2>
              <p className="empty-copy">
                Quick source-grounded metadata for the current live result.
              </p>
            </div>
            <StatusBadge tone="neutral">
              {savedWorkspace
                ? `Saved ${formatPublishedAt(savedWorkspace.saved_at)}`
                : `Retrieved ${formatPublishedAt(workspace.retrieved_at)}`}
            </StatusBadge>
          </div>

          <div className="search-result-meta">
            {overviewRows.map((row) => (
              <div key={row.label} className="overview-block">
                <span className="overview-label">{row.label}</span>
                <strong>{row.value}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="content-grid">
          <article className="card">
            <div className="card-heading">
              <div>
                <h2>Source grounding</h2>
                <p className="empty-copy">
                  Identifiers and provenance for the source record currently opened in
                  RebaTox.
                </p>
              </div>
            </div>

            <div className="study-card-stack">
              <article className="study-card">
                <div className="study-card-copy">
                  <h3>Record identifiers</h3>
                  <p>
                    These identifiers are taken directly from the current live
                    source payload.
                  </p>
                </div>
                <div className="descriptor-list">
                  {workspace.record.identifiers.length > 0 ? (
                    workspace.record.identifiers.map((identifier) => (
                      <div
                        key={`${identifier.namespace}-${identifier.value}`}
                        className="descriptor-row"
                      >
                        <span className="overview-label">{identifier.namespace}</span>
                        <strong>{identifier.value}</strong>
                      </div>
                    ))
                  ) : (
                    <div className="descriptor-row">
                      <span className="overview-label">Identifiers</span>
                      <strong>Not reported</strong>
                    </div>
                  )}
                </div>
              </article>
            </div>
          </article>

          <article className="card">
            <div className="card-heading">
              <div>
                <h2>RebaTox review cue</h2>
                <p className="empty-copy">
                  This live-source workspace is a query-time entry into the broader
                  RebaTox review flow.
                </p>
              </div>
            </div>

            <div className="study-card">
              <div className="study-card-copy">
                <h3>{workspace.review_cue.title}</h3>
                <p>{workspace.review_cue.description}</p>
              </div>
            </div>
          </article>
        </section>

        <section className="card">
          <div className="card-heading">
            <div>
              <h2>Extracted evidence signals</h2>
              <p className="empty-copy">
                Query-time signals distilled from the current source so a reviewer can
                scan the useful evidence before diving into raw sections.
              </p>
            </div>
            <StatusBadge
              tone={workspace.extracted_signals.length > 0 ? "success" : "warning"}
            >
              {workspace.extracted_signals.length} extracted signals
            </StatusBadge>
          </div>

          {workspace.extracted_signals.length === 0 ? (
            <div className="empty-state">
              <div>
                <h3>No extracted signals were available</h3>
                <p className="empty-copy">
                  RebaTox did not infer structured evidence cues from this source
                  payload yet.
                </p>
              </div>
            </div>
          ) : (
            <div className="study-card-stack">
              {workspace.extracted_signals.map((signal) => (
                <article key={signal.key} className="study-card">
                  <div className="study-card-copy">
                    <h3>{signal.label}</h3>
                    <p>{signal.value}</p>
                  </div>
                  <div className="button-row">
                    <StatusBadge
                      tone={
                        signal.confidence === "high"
                          ? "success"
                          : signal.confidence === "medium"
                            ? "warning"
                            : "neutral"
                      }
                    >
                      {signal.confidence} confidence
                    </StatusBadge>
                    {signal.source_section_key ? (
                      <StatusBadge tone="neutral">
                        Section: {signal.source_section_key}
                      </StatusBadge>
                    ) : null}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        {savedWorkspace ? (
          <section className="card">
            <div className="card-heading">
              <div>
                <h2>Saved snapshot details</h2>
                <p className="empty-copy">
                  This workspace was persisted from a live retrieval so the same review
                  snapshot can be reopened later.
                </p>
              </div>
            </div>
            <div className="descriptor-list">
              <div className="descriptor-row">
                <span className="overview-label">Saved workspace id</span>
                <strong>{savedWorkspace.id}</strong>
              </div>
              <div className="descriptor-row">
                <span className="overview-label">Label</span>
                <strong>{savedWorkspace.label}</strong>
              </div>
              <div className="descriptor-row">
                <span className="overview-label">Saved at</span>
                <strong>{formatPublishedAt(savedWorkspace.saved_at)}</strong>
              </div>
            </div>
          </section>
        ) : (
          <WorkspaceSavePanel apiBaseUrl={appConfig.apiBaseUrl} workspace={workspace} />
        )}

        <section className="card">
          <div className="card-heading">
            <div>
              <h2>Source sections</h2>
              <p className="empty-copy">
                Structured source sections pulled into the live RebaTox workspace for
                rapid stewardship review.
              </p>
            </div>
            <StatusBadge tone={workspace.sections.length > 0 ? "success" : "warning"}>
              {workspace.sections.length} sections
            </StatusBadge>
          </div>

          {workspace.sections.length === 0 ? (
            <div className="empty-state">
              <div>
                <h3>No structured sections were available</h3>
                <p className="empty-copy">
                  The current live source record did not expose section-level content
                  for this result.
                </p>
              </div>
            </div>
          ) : (
            <div className="study-card-stack">
              {workspace.sections.map((section) => (
                <article key={section.key} className="study-card">
                  <div className="study-card-copy">
                    <h3>{section.title}</h3>
                  </div>
                  <div className="section-text-stack">
                    {section.content.map((paragraph, index) => (
                      <p key={`${section.key}-${index}`} className="section-text-block">
                        {paragraph}
                      </p>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    );
  } catch (error) {
    return (
      <div className="page-stack">
        <section className="card feedback-banner danger">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Live workspace</span>
              <h2>Source record unavailable</h2>
            </div>
            <StatusBadge tone="danger">API issue</StatusBadge>
          </div>
          <p>{describeLoadError(error)}</p>
          <div className="button-row">
            <Link
              className="button-secondary search-example-link"
              href={buildBackToSearchHref(rawEntityType, query || null)}
            >
              Back to search
            </Link>
          </div>
        </section>
      </div>
    );
  }
}
