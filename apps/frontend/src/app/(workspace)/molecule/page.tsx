import Link from "next/link";

import { PageIntro } from "@/components/page-intro";
import { StatusBadge } from "@/components/status-badge";
import {
  ApiClientError,
  getMoleculeDetail,
  type MoleculeSearchResultResponse,
} from "@/lib/api";
import { appConfig } from "@/lib/config";

type MoleculePageProps = {
  searchParams?: Promise<{
    provider?: string | string[];
    id?: string | string[];
    q?: string | string[];
  }>;
};

function getSingleValue(input: string | string[] | undefined): string {
  const value = Array.isArray(input) ? input[0] : input;
  return (value ?? "").trim();
}

function formatPublishedAt(value: string | null): string {
  if (!value) {
    return "Not reported";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toISOString().slice(0, 10);
}

function describeLoadError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to load the live molecule workspace.";
}

function isSupportedProvider(
  provider: string,
): provider is MoleculeSearchResultResponse["provider"] {
  return provider === "openfda" || provider === "dailymed" || provider === "pubmed";
}

export default async function MoleculePage({ searchParams }: MoleculePageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const provider = getSingleValue(resolvedSearchParams.provider);
  const externalId = getSingleValue(resolvedSearchParams.id);
  const query = getSingleValue(resolvedSearchParams.q);

  if (!provider || !externalId || !isSupportedProvider(provider)) {
    return (
      <div className="page-stack">
        <section className="card feedback-banner danger">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Live molecule workspace</span>
              <h2>Missing molecule selection</h2>
            </div>
            <StatusBadge tone="danger">Input error</StatusBadge>
          </div>
          <p>
            Open this page from molecule search so RebaTox knows which live source
            record to inspect.
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

  try {
    const detail = await getMoleculeDetail(appConfig.apiBaseUrl, provider, externalId);

    return (
      <div className="page-stack">
        <PageIntro
          eyebrow="Live molecule workspace"
          title={detail.molecule.title}
          description={
            detail.molecule.summary ??
            "Live label-backed dossier assembled from the current molecule search result."
          }
          actions={
            <>
              <StatusBadge tone="info">{detail.molecule.provider}</StatusBadge>
              <StatusBadge tone="neutral">
                {detail.molecule.product_type ?? "Label record"}
              </StatusBadge>
            </>
          }
        />

        <section className="card">
          <div className="button-row">
            <Link
              className="button-secondary search-example-link"
              href={query ? `/search?q=${encodeURIComponent(query)}` : "/search"}
            >
              Back to search
            </Link>
            {detail.molecule.source_uri ? (
              <a
                className="button-primary"
                href={detail.molecule.source_uri}
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
              <h2>Molecule overview</h2>
              <p className="empty-copy">
                Quick source-grounded metadata for the current live label record.
              </p>
            </div>
          </div>

          <div className="search-result-meta">
            <div className="overview-block">
              <span className="overview-label">Generic name</span>
              <strong>{detail.molecule.generic_name ?? "Not reported"}</strong>
            </div>
            <div className="overview-block">
              <span className="overview-label">Brand names</span>
              <strong>{detail.molecule.brand_names.join(", ") || "Not reported"}</strong>
            </div>
            <div className="overview-block">
              <span className="overview-label">Manufacturers</span>
              <strong>
                {detail.molecule.manufacturer_names.join(", ") || "Not reported"}
              </strong>
            </div>
            <div className="overview-block">
              <span className="overview-label">Routes</span>
              <strong>{detail.molecule.routes.join(", ") || "Not reported"}</strong>
            </div>
            <div className="overview-block">
              <span className="overview-label">Substances</span>
              <strong>
                {detail.molecule.substance_names.join(", ") || "Not reported"}
              </strong>
            </div>
            <div className="overview-block">
              <span className="overview-label">Label effective date</span>
              <strong>{formatPublishedAt(detail.molecule.published_at)}</strong>
            </div>
          </div>
        </section>

        <section className="content-grid">
          <article className="card">
            <div className="card-heading">
              <div>
                <h2>Source grounding</h2>
                <p className="empty-copy">
                  Identifiers and provenance for the label currently opened in
                  RebaTox.
                </p>
              </div>
            </div>

            <div className="study-card-stack">
              <article className="study-card">
                <div className="study-card-copy">
                  <h3>Record identifiers</h3>
                  <p>
                    These identifiers are taken directly from the current source
                    payload.
                  </p>
                </div>
                <div className="descriptor-list">
                  {detail.molecule.identifiers.length > 0 ? (
                    detail.molecule.identifiers.map((identifier) => (
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
                  This live-source workspace is a search-first entry into the
                  broader RebaTox review flow.
                </p>
              </div>
            </div>

            <div className="study-card">
              <div className="study-card-copy">
                <h3>Current scope</h3>
                <p>
                  This page surfaces live label metadata and structured source
                  sections so stewardship reviewers can inspect a molecule of
                  interest directly. The fuller evidence scoring and report
                  workflow still lives in the seeded review workspace.
                </p>
              </div>
            </div>
          </article>
        </section>

        <section className="card">
          <div className="card-heading">
            <div>
              <h2>Label sections</h2>
              <p className="empty-copy">
                Structured sections pulled from the live source record for rapid
                stewardship review.
              </p>
            </div>
            <StatusBadge tone={detail.sections.length > 0 ? "success" : "warning"}>
              {detail.sections.length} sections
            </StatusBadge>
          </div>

          {detail.sections.length === 0 ? (
            <div className="empty-state">
              <div>
                <h3>No structured sections were available</h3>
                <p className="empty-copy">
                  The current source record did not expose the expected label
                  section fields.
                </p>
              </div>
            </div>
          ) : (
            <div className="study-card-stack">
              {detail.sections.map((section) => (
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
              <span className="section-kicker">Live molecule workspace</span>
              <h2>Molecule record unavailable</h2>
            </div>
            <StatusBadge tone="danger">API issue</StatusBadge>
          </div>
          <p>{describeLoadError(error)}</p>
          <div className="button-row">
            <Link
              className="button-secondary search-example-link"
              href={query ? `/search?q=${encodeURIComponent(query)}` : "/search"}
            >
              Back to search
            </Link>
          </div>
        </section>
      </div>
    );
  }
}
