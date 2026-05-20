import type { LiveSearchResponse } from "@/lib/api";
import {
  formatPublishedAt,
  getProviderLabel,
  groupSearchResultsByProvider,
} from "@/lib/live-workspace";

import { StatusBadge } from "./status-badge";

type LiveSearchResultsProps = { response: LiveSearchResponse };

export function LiveSearchResults({ response }: LiveSearchResultsProps) {
  const groups = groupSearchResultsByProvider(response.items);

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
      {groups.map((group) => (
        <section key={group.provider} className="results-group">
          <div className="card-heading">
            <div>
              <h3>{group.label}</h3>
              <p className="empty-copy">
                {group.items.length} alternative match{group.items.length === 1 ? "" : "es"} from{" "}
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

                {item.source_uri && item.provider !== "openfda" ? (
                  <div className="button-row">
                    <a
                      className="button-secondary search-example-link"
                      href={item.source_uri}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open source
                    </a>
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
