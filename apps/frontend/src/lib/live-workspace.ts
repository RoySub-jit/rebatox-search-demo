import type {
  LiveSearchResultResponse,
  LiveWorkspaceResponse,
  SearchEntityType,
} from "@/lib/api";

export type SearchModeConfig = {
  value: SearchEntityType;
  label: string;
  title: string;
  description: string;
  queryPlaceholder: string;
  examples: string[];
  emptyStateTitle: string;
  emptyStateDescription: string;
};

export type GroupedLiveSearchResults = {
  provider: LiveSearchResultResponse["provider"];
  label: string;
  items: LiveSearchResultResponse[];
};

export type WorkspaceOverviewRow = {
  label: string;
  value: string;
};

export const SEARCH_MODE_CONFIGS: SearchModeConfig[] = [
  {
    value: "molecule",
    label: "Molecule",
    title: "Search a molecule",
    description:
      "Search live source records for a molecule, then open a source-grounded RebaTox workspace.",
    queryPlaceholder: "Search aspirin, adalimumab, ibuprofen...",
    examples: ["aspirin", "ibuprofen", "adalimumab"],
    emptyStateTitle: "Start with a molecule name",
    emptyStateDescription:
      "Search a brand, generic, or substance name to inspect a live source-backed molecule workspace.",
  },
  {
    value: "degradant",
    label: "Degradant",
    title: "Search a degradant",
    description:
      "Search live literature for degradant-specific signals and open a transient evidence workspace.",
    queryPlaceholder: "Search NDMA, acetamide, formaldehyde...",
    examples: ["ndma", "acetamide", "formaldehyde"],
    emptyStateTitle: "Start with a degradant term",
    emptyStateDescription:
      "Search a degradant, impurity, or breakdown product to inspect live literature before saving a review workspace.",
  },
  {
    value: "el",
    label: "E&L",
    title: "Search an E&L topic",
    description:
      "Search live evidence for extractables and leachables topics, then review the result in context.",
    queryPlaceholder: "Search bisphenol a, DEHP, leachables...",
    examples: ["bisphenol a", "dehp", "leachables"],
    emptyStateTitle: "Start with an E&L topic",
    emptyStateDescription:
      "Search an extractable, leachable, or packaging migrant to inspect live source material directly.",
  },
];

const PROVIDER_LABELS: Record<LiveSearchResultResponse["provider"], string> = {
  dailymed: "DailyMed",
  openfda: "openFDA",
  pubmed: "PubMed",
};

export function isSearchEntityType(value: string): value is SearchEntityType {
  return value === "molecule" || value === "degradant" || value === "el";
}

export function getSearchModeConfig(entityType: SearchEntityType): SearchModeConfig {
  return (
    SEARCH_MODE_CONFIGS.find((config) => config.value === entityType) ??
    SEARCH_MODE_CONFIGS[0]
  );
}

export function getProviderLabel(
  provider: LiveSearchResultResponse["provider"],
): string {
  return PROVIDER_LABELS[provider] ?? provider;
}

export function groupSearchResultsByProvider(
  items: LiveSearchResultResponse[],
): GroupedLiveSearchResults[] {
  const groups = new Map<
    LiveSearchResultResponse["provider"],
    GroupedLiveSearchResults
  >();

  for (const item of items) {
    const existing = groups.get(item.provider);
    if (existing) {
      existing.items.push(item);
      continue;
    }

    groups.set(item.provider, {
      provider: item.provider,
      label: getProviderLabel(item.provider),
      items: [item],
    });
  }

  return Array.from(groups.values());
}

export function formatPublishedAt(value: string | null): string {
  if (!value) {
    return "Not reported";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toISOString().slice(0, 10);
}

function joinOrDefault(values: string[], fallback = "Not reported"): string {
  return values.join(", ") || fallback;
}

export function buildWorkspaceOverviewRows(
  workspace: LiveWorkspaceResponse,
): WorkspaceOverviewRow[] {
  const { record } = workspace;

  if (workspace.entity_type === "molecule") {
    return [
      { label: "Generic name", value: record.generic_name ?? "Not reported" },
      { label: "Brand names", value: joinOrDefault(record.brand_names) },
      {
        label: "Manufacturers",
        value: joinOrDefault(record.manufacturer_names),
      },
      { label: "Routes", value: joinOrDefault(record.routes) },
      { label: "Substances", value: joinOrDefault(record.substance_names) },
      { label: "Published date", value: formatPublishedAt(record.published_at) },
    ];
  }

  return [
    { label: "Journal", value: record.journal ?? "Not reported" },
    { label: "Authors", value: joinOrDefault(record.authors) },
    { label: "Document type", value: record.document_type ?? "Not reported" },
    { label: "Keywords", value: joinOrDefault(record.keywords) },
    { label: "Published date", value: formatPublishedAt(record.published_at) },
  ];
}
