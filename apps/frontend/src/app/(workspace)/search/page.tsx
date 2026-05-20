import Link from "next/link";

import { LiveSearchResults } from "@/components/live-search-results";
import { PageIntro } from "@/components/page-intro";
import { SearchModeSwitcher } from "@/components/search-mode-switcher";
import { StatusBadge } from "@/components/status-badge";
import {
  ApiClientError,
  searchLiveRecords,
  type LiveSearchResponse,
} from "@/lib/api";
import { appConfig } from "@/lib/config";
import {
  getSearchModeConfig,
  isSearchEntityType,
  type SearchModeConfig,
} from "@/lib/live-workspace";

type SearchPageProps = {
  searchParams?: Promise<{
    entity_type?: string | string[];
    q?: string | string[];
  }>;
};

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

  return "Unable to load live search results.";
}

function getModeConfig(rawMode: string): SearchModeConfig {
  if (isSearchEntityType(rawMode)) {
    return getSearchModeConfig(rawMode);
  }

  return getSearchModeConfig("molecule");
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const query = getQueryValue(resolvedSearchParams.q);
  const rawEntityType = getQueryValue(resolvedSearchParams.entity_type) || "molecule";
  const modeConfig = getModeConfig(rawEntityType);

  let loadError: string | null = null;
  let response: LiveSearchResponse | null = null;

  if (query.length >= 2) {
    try {
      response = await searchLiveRecords(appConfig.apiBaseUrl, modeConfig.value, query, 8);
    } catch (error) {
      loadError = describeLoadError(error);
    }
  }

  return (
    <div className="page-stack">
      <PageIntro
        eyebrow="Live source search"
        title={modeConfig.title}
        description={modeConfig.description}
        actions={
          <>
            <StatusBadge tone="info">Live retrieval</StatusBadge>
            <StatusBadge tone="neutral">Prototype</StatusBadge>
          </>
        }
      />

      <section className="card search-panel">
        <div className="card-heading">
          <div>
            <h2>Choose a search mode</h2>
            <p className="empty-copy">
              RebaTox now supports query-time search for molecules, degradants, and
              E&amp;L topics without bulk source ingestion.
            </p>
          </div>
          <StatusBadge tone="neutral">{modeConfig.label}</StatusBadge>
        </div>

        <SearchModeSwitcher currentMode={modeConfig.value} currentQuery={query} />

        <div className="card-heading search-panel-subhead">
          <div>
            <h2>Find an entity of interest</h2>
            <p className="empty-copy">
              Search live public sources, then open a transient workspace grounded in
              the selected source record.
            </p>
          </div>
          <StatusBadge tone="neutral">Query-based</StatusBadge>
        </div>

        <form action="/search" method="GET" className="search-form">
          <input type="hidden" name="entity_type" value={modeConfig.value} />
          <div className="search-form-row">
            <input
              className="input-control search-input"
              type="search"
              name="q"
              defaultValue={query}
              placeholder={modeConfig.queryPlaceholder}
              aria-label={`Search ${modeConfig.label.toLowerCase()}`}
            />
            <button className="button-primary" type="submit">
              Search
            </button>
          </div>
        </form>

        <div className="button-row">
          {modeConfig.examples.map((example) => (
            <Link
              key={example}
              href={`/search?entity_type=${modeConfig.value}&q=${encodeURIComponent(example)}`}
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
            <h2>{modeConfig.emptyStateTitle}</h2>
            <p className="empty-copy">{modeConfig.emptyStateDescription}</p>
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
          <p>Use at least 2 characters for a live search.</p>
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
            Confirm the backend is running and can reach the configured public source
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

          <LiveSearchResults response={response} />
        </section>
      ) : null}
    </div>
  );
}
