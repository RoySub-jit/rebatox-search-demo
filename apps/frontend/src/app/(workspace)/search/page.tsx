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
    } catch (error) {
      loadError = describeLoadError(error);
    }
  }

  const primaryResult = response?.items.length
    ? getPrimarySearchResult(modeConfig.value, response.items)
    : null;
  const alternativeResults =
    response && primaryResult
      ? response.items.filter(
          (item) =>
            !(
              item.provider === primaryResult.provider &&
              item.external_id === primaryResult.external_id
            ),
        )
      : response?.items ?? [];

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
              Search live public sources. RebaTox highlights the strongest current
              match first, with an option to review the other source matches if needed.
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

      {response?.warnings.length ? (
        <section className="card feedback-banner warning">
          <div className="card-heading">
            <div>
              <h2>Partial live source coverage</h2>
            </div>
            <StatusBadge tone="warning">Upstream warning</StatusBadge>
          </div>
          <div className="section-text-stack">
            {response.warnings.map((warning, index) => (
              <p key={`search-warning-${index}`}>{warning}</p>
            ))}
          </div>
        </section>
      ) : null}

      {response && primaryResult ? (
        <section className="card">
          <div className="card-heading">
            <div>
              <h2>Best current match</h2>
              <p className="empty-copy">
                RebaTox selected the strongest current source-backed workspace for{" "}
                <strong>{response.query}</strong>.
              </p>
            </div>
            <StatusBadge tone="success">
              {primaryResult.provider}
            </StatusBadge>
          </div>

          <article className="task-item">
            <div className="task-item-top">
              <div>
                <h3>{primaryResult.title}</h3>
                <p>
                  {primaryResult.summary ??
                    primaryResult.subtitle ??
                    "No summary snippet was available in the current source payload."}
                </p>
              </div>
              <div className="badge-row">
                <StatusBadge tone="info">{primaryResult.provider}</StatusBadge>
                {primaryResult.document_type ? (
                  <StatusBadge tone="neutral">{primaryResult.document_type}</StatusBadge>
                ) : null}
              </div>
            </div>

            <div className="search-result-meta">
              {primaryResult.generic_name ? (
                <div className="overview-block">
                  <span className="overview-label">Generic</span>
                  <strong>{primaryResult.generic_name}</strong>
                </div>
              ) : null}
              {primaryResult.brand_names.length > 0 ? (
                <div className="overview-block">
                  <span className="overview-label">Brands</span>
                  <strong>{primaryResult.brand_names.join(", ")}</strong>
                </div>
              ) : null}
              {primaryResult.journal ? (
                <div className="overview-block">
                  <span className="overview-label">Journal</span>
                  <strong>{primaryResult.journal}</strong>
                </div>
              ) : null}
              <div className="overview-block">
                <span className="overview-label">Published</span>
                <strong>{primaryResult.published_at ?? "Not reported"}</strong>
              </div>
            </div>

            <div className="button-row">
              <Link
                className="button-primary"
                href={`/workspace?entity_type=${primaryResult.entity_type}&provider=${primaryResult.provider}&id=${encodeURIComponent(primaryResult.external_id)}&q=${encodeURIComponent(response.query)}`}
              >
                Open best match in RebaTox
              </Link>
              {primaryResult.source_uri && primaryResult.provider !== "openfda" ? (
                <a
                  className="button-secondary search-example-link"
                  href={primaryResult.source_uri}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open source
                </a>
              ) : null}
              {alternativeResults.length > 0 && !showResults ? (
                <Link
                  className="button-secondary search-example-link"
                  href={`/search?entity_type=${response.entity_type}&q=${encodeURIComponent(response.query)}&results=1`}
                >
                  View {alternativeResults.length} other match{alternativeResults.length === 1 ? "" : "es"}
                </Link>
              ) : null}
            </div>
          </article>
        </section>
      ) : null}

      {response && !primaryResult ? (
        <section className="card">
          <div className="card-heading">
            <div>
              <h2>No high-confidence live match</h2>
              <p className="empty-copy">
                RebaTox did not find a strong current workspace for{" "}
                <strong>{response.query}</strong>. You can still review any low-signal
                source matches below.
              </p>
            </div>
            <StatusBadge tone="warning">No primary match</StatusBadge>
          </div>

          <LiveSearchResults response={response} />
        </section>
      ) : null}

      {response && primaryResult && showResults ? (
        <section className="card">
          <div className="card-heading">
            <div>
              <h2>Other source matches</h2>
              <p className="empty-copy">
                Compare alternate live sources for <strong>{response.query}</strong>.
              </p>
            </div>
            <StatusBadge tone={alternativeResults.length > 0 ? "success" : "warning"}>
              {alternativeResults.length} alternative matches
            </StatusBadge>
          </div>

          <LiveSearchResults
            response={{
              ...response,
              total_results: alternativeResults.length,
              items: alternativeResults,
            }}
          />
        </section>
      ) : null}
    </div>
  );
}
