import Link from "next/link";

import { PageIntro } from "@/components/page-intro";
import { StatusBadge } from "@/components/status-badge";
import {
  ApiClientError,
  resolveLiveWorkspace,
  type LiveSearchResultResponse,
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

export default async function WorkspacePage({ searchParams }: WorkspacePageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const rawEntityType = getSingleValue(resolvedSearchParams.entity_type) || "molecule";
  const provider = getSingleValue(resolvedSearchParams.provider);
  const externalId = getSingleValue(resolvedSearchParams.id);
  const query = getSingleValue(resolvedSearchParams.q);

  if (
    !isSearchEntityType(rawEntityType) ||
    !provider ||
    !externalId ||
    !isSupportedProvider(provider)
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

  const modeConfig = getSearchModeConfig(rawEntityType);

  try {
    const workspace = await resolveLiveWorkspace(appConfig.apiBaseUrl, {
      entity_type: rawEntityType,
      provider,
      external_id: externalId,
      query: query || null,
    });
    const overviewRows = buildWorkspaceOverviewRows(workspace);

    return (
      <div className="page-stack">
        <PageIntro
          eyebrow={`Live ${modeConfig.label.toLowerCase()} workspace`}
          title={workspace.record.title}
          description={
            workspace.record.summary ??
            "Live source-backed workspace assembled from the current RebaTox query."
          }
          actions={
            <>
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

        <section className="card">
          <div className="button-row">
            <Link
              className="button-secondary search-example-link"
              href={
                query
                  ? `/search?entity_type=${rawEntityType}&q=${encodeURIComponent(query)}`
                  : `/search?entity_type=${rawEntityType}`
              }
            >
              Back to search
            </Link>
            {workspace.record.source_uri ? (
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
              Retrieved {formatPublishedAt(workspace.retrieved_at)}
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
              href={
                query
                  ? `/search?entity_type=${rawEntityType}&q=${encodeURIComponent(query)}`
                  : `/search?entity_type=${rawEntityType}`
              }
            >
              Back to search
            </Link>
          </div>
        </section>
      </div>
    );
  }
}
