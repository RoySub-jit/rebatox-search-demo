import Link from "next/link";

import { PageIntro } from "@/components/page-intro";
import { StatusBadge } from "@/components/status-badge";
import {
  ApiClientError,
  searchMolecules,
  type MoleculeSearchResponse,
} from "@/lib/api";
import { appConfig } from "@/lib/config";

type SearchPageProps = {
  searchParams?: Promise<{
    q?: string | string[];
  }>;
};

const EXAMPLE_QUERIES = ["aspirin", "ibuprofen", "adalimumab"];

function getQueryValue(input: string | string[] | undefined): string {
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

  return "Unable to load molecule search results.";
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const query = getQueryValue(resolvedSearchParams.q);

  let loadError: string | null = null;
  let response: MoleculeSearchResponse | null = null;

  if (query.length >= 2) {
    try {
      response = await searchMolecules(appConfig.apiBaseUrl, query, 8);
    } catch (error) {
      loadError = describeLoadError(error);
    }
  }

  return (
    <div className="page-stack">
      <PageIntro
        eyebrow="Live source search"
        title="Search a molecule"
        description="Search live openFDA label metadata by brand, generic, or substance name, then open the result in a RebaTox review workspace."
        actions={
          <>
            <StatusBadge tone="info">openFDA live</StatusBadge>
            <StatusBadge tone="neutral">Prototype</StatusBadge>
          </>
        }
      />

      <section className="card search-panel">
        <div className="card-heading">
          <div>
            <h2>Find a molecule of interest</h2>
            <p className="empty-copy">
              Enter a brand name, generic name, or active substance to search the
              live label source.
            </p>
          </div>
          <StatusBadge tone="neutral">Query-based</StatusBadge>
        </div>

        <form action="/search" method="GET" className="search-form">
          <div className="search-form-row">
            <input
              className="input-control search-input"
              type="search"
              name="q"
              defaultValue={query}
              placeholder="Search aspirin, adalimumab, ibuprofen..."
              aria-label="Search molecule"
            />
            <button className="button-primary" type="submit">
              Search
            </button>
          </div>
        </form>

        <div className="button-row">
          {EXAMPLE_QUERIES.map((example) => (
            <Link
              key={example}
              href={`/search?q=${encodeURIComponent(example)}`}
              className="button-secondary search-example-link"
            >
              Try {example}
            </Link>
          ))}
        </div>
      </section>

      {query.length === 0 ? (
        <section className="card empty-state">
          <div>
            <h2>Start with a molecule name</h2>
            <p className="empty-copy">
              This searchable prototype is the quickest path for stewardship
              reviewers to open RebaTox and inspect a real label-backed molecule.
            </p>
          </div>
        </section>
      ) : null}

      {query.length > 0 && query.length < 2 ? (
        <section className="card feedback-banner danger">
          <div className="card-heading">
            <div>
              <h2>Search term is too short</h2>
            </div>
            <StatusBadge tone="danger">Input error</StatusBadge>
          </div>
          <p>Use at least 2 characters for a live molecule lookup.</p>
        </section>
      ) : null}

      {loadError ? (
        <section className="card feedback-banner danger">
          <div className="card-heading">
            <div>
              <h2>Search unavailable</h2>
            </div>
            <StatusBadge tone="danger">API issue</StatusBadge>
          </div>
          <p>{loadError}</p>
          <p>
            Confirm the backend is running and can reach the external label source
            before retrying this lookup.
          </p>
        </section>
      ) : null}

      {response ? (
        <section className="card">
          <div className="card-heading">
            <div>
              <h2>Search results</h2>
              <p className="empty-copy">
                Showing {response.items.length} live matches for{" "}
                <strong>{response.query}</strong>.
              </p>
            </div>
            <StatusBadge tone={response.items.length > 0 ? "success" : "warning"}>
              {response.total_results} source matches
            </StatusBadge>
          </div>

          {response.items.length === 0 ? (
            <div className="empty-state">
              <div>
                <h3>No live matches found</h3>
                <p className="empty-copy">
                  Try a broader generic name, substance name, or a different brand
                  spelling.
                </p>
              </div>
            </div>
          ) : (
            <div className="results-stack">
              {response.items.map((item) => (
                <article key={`${item.provider}-${item.external_id}`} className="task-item">
                  <div className="task-item-top">
                    <div>
                      <h3>{item.title}</h3>
                      <p>
                        {item.summary ??
                          "No summary snippet was available in the current source payload."}
                      </p>
                    </div>
                    <div className="badge-row">
                      <StatusBadge tone="info">{item.provider}</StatusBadge>
                      {item.product_type ? (
                        <StatusBadge tone="neutral">{item.product_type}</StatusBadge>
                      ) : null}
                    </div>
                  </div>

                  <div className="search-result-meta">
                    <div className="overview-block">
                      <span className="overview-label">Generic</span>
                      <strong>{item.generic_name ?? "Not reported"}</strong>
                    </div>
                    <div className="overview-block">
                      <span className="overview-label">Brands</span>
                      <strong>{item.brand_names.join(", ") || "Not reported"}</strong>
                    </div>
                    <div className="overview-block">
                      <span className="overview-label">Manufacturer</span>
                      <strong>
                        {item.manufacturer_names.join(", ") || "Not reported"}
                      </strong>
                    </div>
                    <div className="overview-block">
                      <span className="overview-label">Routes</span>
                      <strong>{item.routes.join(", ") || "Not reported"}</strong>
                    </div>
                  </div>

                  <div className="button-row">
                    <Link
                      className="button-primary"
                      href={`/molecule?provider=${item.provider}&id=${encodeURIComponent(item.external_id)}&q=${encodeURIComponent(response.query)}`}
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
          )}
        </section>
      ) : null}
    </div>
  );
}
