import Link from "next/link";

import type { LiveSearchResponse } from "@/lib/api";
import {
  formatPublishedAt,
  getPrimarySearchResult,
  getProviderLabel,
  groupSearchResultsByProvider,
} from "@/lib/live-workspace";

import { StatusBadge } from "./status-badge";

type LiveSearchResultsProps = {
  response: LiveSearchResponse;
};

function buildWorkspaceHref(
  entityType: string,
  provider: string,
  externalId: string,
  query: string,
): string {
  return `/workspace?entity_type=${entityType}&provider=${provider}&id=${encodeURIComponent(externalId)}&q=${encodeURIComponent(query)}`;
}

export function LiveSearchResults({ response }: LiveSearchResultsProps) {
  const groups = groupSearchResultsByProvider(response.items);
  const primaryResult = getPrimarySearchResult(response.entity_type, response.items);

  if (response.items.length === 0) {
    return (
      <div className="empty-state">
        <div>
          <h3>No live matches found</h3>
          <p className="empty-copy">
            Try a broader search term, a related synonym, or a different source-backed
            entity name.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="results-stack">
      {primaryResult ? (
        <section className="card results-highlight">
          <div className="card-heading">
            <div>
              <h3>Best match</h3>
              <p className="empty-copy">
                RebaTox picked the clearest current source record so you can open one
                strong workspace path immediately.
              </p>
            </div>
            <StatusBadge tone="success">{getProviderLabel(primaryResult.provider)}</StatusBadge>
          </div>
          <div className="task-item">
            <div className="task-item-top">
              <div>
                <h4>{primaryResult.title}</h4>
                <p>
                  {primaryResult.summary ??
                    primaryResult.subtitle ??
                    "No summary snippet was available in the current source payload."}
                </p>
              </div>
            </div>
            <div className="button-row">
              <Link
                className="button-primary"
                href={buildWorkspaceHref(
                  response.entity_type,
                  primaryResult.provider,
                  primaryResult.external_id,
                  response.query,
                )}
              >
                Open best match in RebaTox
              </Link>
              {primaryResult.source_uri ? (
                <a
                  className="button-secondary search-example-link"
                  href={primaryResult.source_uri}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open source
                </a>
              ) : null}
            </div>
          </div>
        </section>
      ) : null}

      {groups.map((group) => (
        <section key={group.provider} className="results-group">
          <div className="card-heading">
            <div>
              <h3>{group.label}</h3>
              <p className="empty-copy">
                {group.items.length} live result{group.items.length === 1 ? "" : "s"} from{" "}
                {getProviderLabel(group.provider)}.
              </p>
            </div>
            <StatusBadge tone="info">{group.label}</StatusBadge>
          </div>

          <div className="results-stack">
            {group.items.map((item) => (
              <article key={`${item.provider}-${item.external_id}`} className="task-item">
                <div className="task-item-top">
                  <div>
                    <h4>{item.title}</h4>
                    <p>
                      {item.summary ??
                        item.subtitle ??
                        "No summary snippet was available in the current source payload."}
                    </p>
                  </div>
                  <div className="badge-row">
                    <StatusBadge tone="info">{item.provider}</StatusBadge>
                    {item.document_type ? (
                      <StatusBadge tone="neutral">{item.document_type}</StatusBadge>
                    ) : null}
                  </div>
                </div>

                <div className="search-result-meta">
                  {item.generic_name ? (
                    <div className="overview-block">
                      <span className="overview-label">Generic</span>
                      <strong>{item.generic_name}</strong>
                    </div>
                  ) : null}
                  {item.brand_names.length > 0 ? (
                    <div className="overview-block">
                      <span className="overview-label">Brands</span>
                      <strong>{item.brand_names.join(", ")}</strong>
                    </div>
                  ) : null}
                  {item.journal ? (
                    <div className="overview-block">
                      <span className="overview-label">Journal</span>
                      <strong>{item.journal}</strong>
                    </div>
                  ) : null}
                  {item.authors.length > 0 ? (
                    <div className="overview-block">
                      <span className="overview-label">Authors</span>
                      <strong>{item.authors.slice(0, 3).join(", ")}</strong>
                    </div>
                  ) : null}
                  <div className="overview-block">
                    <span className="overview-label">Published</span>
                    <strong>{formatPublishedAt(item.published_at)}</strong>
                  </div>
                </div>

                <div className="button-row">
                  <Link
                    className="button-primary"
                    href={buildWorkspaceHref(
                      response.entity_type,
                      item.provider,
                      item.external_id,
                      response.query,
                    )}
                  >
                    Open in RebaTox
                  </Link>
                  {item.source_uri ? (
                    <a
                      className="button-secondary search-example-link"
                      href={item.source_uri}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open source
                    </a>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
