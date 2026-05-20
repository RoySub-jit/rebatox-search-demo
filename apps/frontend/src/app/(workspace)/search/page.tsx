import Link from "next/link";
import { redirect } from "next/navigation";
import { isRedirectError } from "next/dist/client/components/redirect-error";

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
  getPrimarySearchResult,
  getSearchModeConfig,
  isSearchEntityType,
  type SearchModeConfig,
} from "@/lib/live-workspace";

type SearchPageProps = {
  searchParams?: Promise<{
    entity_type?: string | string[];
    q?: string | string[];
    results?: string | string[];
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

function getModeHighlights(mode: SearchModeConfig) {
  if (mode.value === "molecule") {
    return [
      {
        label: "Live sources",
        value: "openFDA, DailyMed, PubChem, PubMed, ECHA",
        copy: "Blend label-backed records, chemical identity data, literature, and regulatory context so a reviewer can start with the strongest current public evidence.",
      },
      {
        label: "Workspace output",
        value: "One review-ready record",
        copy: "RebaTox resolves the strongest current match into a structured workspace instead of leaving reviewers in raw source text.",
      },
      {
        label: "Reviewer objective",
        value: "Fast triage to formal review",
        copy: "Use the workspace to scan route, manufacturer, dose language, warnings, and extracted safety cues before saving a snapshot.",
      },
    ];
  }

  if (mode.value === "degradant") {
    return [
      {
        label: "Live sources",
        value: "PubMed plus ECHA regulatory lookup",
        copy: "Search degradant-relevant abstracts and add a regulatory handoff path for classification-oriented follow-up.",
      },
      {
        label: "Workspace output",
        value: "Evidence cues and POD language",
        copy: "Dose, exposure, and point-of-departure language are surfaced first so the tox reviewer can decide whether the hit is worth deeper follow-up.",
      },
      {
        label: "Reviewer objective",
        value: "Rapid degradant signal scan",
        copy: "Support early impurity review without waiting for a batch-ingestion job or manual literature notes.",
      },
    ];
  }

  return [
    {
      label: "Live sources",
      value: "PubMed plus ECHA regulatory lookup",
      copy: "Search public literature for extractables and leachables topics and keep a direct regulatory lookup path available inside the same workflow.",
    },
    {
      label: "Workspace output",
      value: "Source-grounded E&L workspace",
      copy: "Normalize source details, extracted signals, and provenance so the same topic can be reopened or shared with reviewers.",
    },
    {
      label: "Reviewer objective",
      value: "Early packaging risk framing",
      copy: "Use query-time evidence retrieval to assess whether an E&L topic merits a saved workspace and fuller toxicology review.",
    },
  ];
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const query = getQueryValue(resolvedSearchParams.q);
  const rawEntityType = getQueryValue(resolvedSearchParams.entity_type) || "molecule";
  const showResults = getQueryValue(resolvedSearchParams.results) === "1";
  const modeConfig = getModeConfig(rawEntityType);
  const modeHighlights = getModeHighlights(modeConfig);

  let loadError: string | null = null;
  let response: LiveSearchResponse | null = null;

  if (query.length >= 2) {
    try {
      response = await searchLiveRecords(appConfig.apiBaseUrl, modeConfig.value, query, 8);
      const primaryResult = response.items.length
        ? getPrimarySearchResult(modeConfig.value, response.items)
        : null;
      if (appConfig.publicDemoMode && primaryResult && !showResults) {
        redirect(
          `/workspace?entity_type=${response.entity_type}&provider=${primaryResult.provider}&id=${encodeURIComponent(primaryResult.external_id)}&q=${encodeURIComponent(response.query)}`,
        );
      }
    } catch (error) {
      if (isRedirectError(error)) {
        throw error;
      }
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

      <section className="executive-summary-grid">
        {modeHighlights.map((highlight) => (
          <article key={highlight.label} className="executive-summary-card">
            <span className="executive-summary-eyebrow">{highlight.label}</span>
            <strong className="executive-summary-value">{highlight.value}</strong>
            <p className="executive-summary-copy">{highlight.copy}</p>
          </article>
        ))}
      </section>

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
              Search live public sources. RebaTox will open the strongest current match
              directly, with an option to review all other matches if needed.
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

        <div className="button-row search-example-row">
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
