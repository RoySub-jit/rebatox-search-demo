const { test } = require("node:test");
const assert = require("node:assert/strict");

const {
  buildPodCurationRows,
  buildWorkspaceOverviewRows,
  formatPublishedAt,
  getPrimarySearchResult,
  getProviderLabel,
  getSearchModeConfig,
  groupSearchResultsByProvider,
  isSearchEntityType,
} = require("./live-workspace.ts");

test("live-workspace helpers expose search mode configs", () => {
  assert.equal(isSearchEntityType("molecule"), true);
  assert.equal(isSearchEntityType("degradant"), true);
  assert.equal(isSearchEntityType("el"), true);
  assert.equal(isSearchEntityType("something-else"), false);

  assert.equal(getSearchModeConfig("molecule").examples[0], "aspirin");
  assert.equal(getSearchModeConfig("degradant").examples[0], "ndma");
  assert.equal(getSearchModeConfig("el").examples[0], "bisphenol a");
});

test("live-workspace helpers group mixed-source results", () => {
  const grouped = groupSearchResultsByProvider([
    {
      entity_type: "molecule",
      provider: "openfda",
      external_id: "set-1",
      title: "Aspirin Label",
      subtitle: "HUMAN OTC DRUG",
      summary: null,
      document_type: "label_record",
      published_at: "2026-04-24",
      source_uri: "https://example.test/openfda/set-1",
      identifiers: [],
      generic_name: "aspirin",
      brand_names: ["Aspirin"],
      manufacturer_names: [],
      routes: ["ORAL"],
      substance_names: ["ASPIRIN"],
      product_type: "HUMAN OTC DRUG",
      authors: [],
      journal: null,
      keywords: [],
    },
    {
      entity_type: "molecule",
      provider: "pubmed",
      external_id: "12345",
      title: "Aspirin Review",
      subtitle: "Journal of Safety",
      summary: "Journal of Safety | Lead author: Doe J",
      document_type: "journal_article",
      published_at: "2025-06-01",
      source_uri: "https://pubmed.ncbi.nlm.nih.gov/12345/",
      identifiers: [],
      generic_name: null,
      brand_names: [],
      manufacturer_names: [],
      routes: [],
      substance_names: [],
      product_type: null,
      authors: ["Doe J"],
      journal: "Journal of Safety",
      keywords: [],
    },
  ]);

  assert.equal(grouped.length, 2);
  assert.equal(grouped[0].label, "openFDA");
  assert.equal(grouped[1].label, "PubMed");
  assert.equal(getProviderLabel("openfda"), "openFDA");
});

test("live-workspace helpers choose a primary match for direct opening", () => {
  const items = [
    {
      entity_type: "molecule",
      provider: "pubmed",
      external_id: "12345",
      title: "Aspirin Review",
      subtitle: "Journal of Safety",
      summary: "Journal of Safety | Lead author: Doe J",
      document_type: "journal_article",
      published_at: "2025-06-01",
      source_uri: "https://pubmed.ncbi.nlm.nih.gov/12345/",
      identifiers: [],
      generic_name: null,
      brand_names: [],
      manufacturer_names: [],
      routes: [],
      substance_names: [],
      product_type: null,
      authors: ["Doe J"],
      journal: "Journal of Safety",
      keywords: [],
    },
    {
      entity_type: "molecule",
      provider: "openfda",
      external_id: "set-1",
      title: "Aspirin Label",
      subtitle: "HUMAN OTC DRUG",
      summary: null,
      document_type: "label_record",
      published_at: "2026-04-24",
      source_uri: "https://example.test/openfda/set-1",
      identifiers: [],
      generic_name: "aspirin",
      brand_names: ["Aspirin"],
      manufacturer_names: [],
      routes: ["ORAL"],
      substance_names: ["ASPIRIN"],
      product_type: "HUMAN OTC DRUG",
      authors: [],
      journal: null,
      keywords: [],
    },
  ];

  assert.equal(getPrimarySearchResult("molecule", items)?.provider, "openfda");
  assert.equal(getPrimarySearchResult("degradant", items)?.provider, "pubmed");
});

test("live-workspace helpers build overview rows for molecule and literature modes", () => {
  const moleculeRows = buildWorkspaceOverviewRows({
    entity_type: "molecule",
    query: "aspirin",
    record: {
      entity_type: "molecule",
      provider: "openfda",
      external_id: "set-1",
      title: "Aspirin Label",
      subtitle: "HUMAN OTC DRUG",
      summary: null,
      document_type: "label_record",
      published_at: "2026-04-24",
      source_uri: "https://example.test/openfda/set-1",
      identifiers: [],
      generic_name: "aspirin",
      brand_names: ["Aspirin"],
      manufacturer_names: ["Example Labs"],
      routes: ["ORAL"],
      substance_names: ["ASPIRIN"],
      product_type: "HUMAN OTC DRUG",
      authors: [],
      journal: null,
      keywords: [],
    },
    sections: [],
    review_cue: {
      title: "Label-backed stewardship review",
      description: "Review the live label record.",
    },
    retrieval_mode: "live",
    retrieved_at: "2026-05-08T12:00:00Z",
  });

  const literatureRows = buildWorkspaceOverviewRows({
    entity_type: "degradant",
    query: "ndma",
    record: {
      entity_type: "degradant",
      provider: "pubmed",
      external_id: "12345",
      title: "NDMA Risk Review",
      subtitle: "Journal of Safety",
      summary: "Lead author: Doe J",
      document_type: "journal_article",
      published_at: "2025-06-01",
      source_uri: "https://pubmed.ncbi.nlm.nih.gov/12345/",
      identifiers: [],
      generic_name: null,
      brand_names: [],
      manufacturer_names: [],
      routes: [],
      substance_names: [],
      product_type: null,
      authors: ["Doe J", "Smith A"],
      journal: "Journal of Safety",
      keywords: ["ndma"],
    },
    sections: [],
    review_cue: {
      title: "Literature-backed evidence review",
      description: "Review the live article.",
    },
    retrieval_mode: "live",
    retrieved_at: "2026-05-08T12:00:00Z",
  });

  assert.equal(moleculeRows[0].label, "Generic name");
  assert.equal(moleculeRows[0].value, "aspirin");
  assert.equal(literatureRows[0].label, "Journal");
  assert.equal(literatureRows[0].value, "Journal of Safety");
  assert.equal(formatPublishedAt("2026-04-24"), "2026-04-24");
  assert.equal(formatPublishedAt(null), "Not reported");
});

test("live-workspace helpers build a POD curation snapshot from extracted signals", () => {
  const rows = buildPodCurationRows({
    entity_type: "molecule",
    query: "aspirin",
    record: {
      entity_type: "molecule",
      provider: "pubmed",
      external_id: "12345",
      title: "Aspirin Review",
      subtitle: "Journal of Safety",
      summary: "Lead author: Doe J",
      document_type: "journal_article",
      published_at: "2025-06-01",
      source_uri: "https://pubmed.ncbi.nlm.nih.gov/12345/",
      identifiers: [],
      generic_name: null,
      brand_names: [],
      manufacturer_names: [],
      routes: ["ORAL"],
      substance_names: [],
      product_type: null,
      authors: ["Doe J"],
      journal: "Journal of Safety",
      keywords: ["aspirin"],
    },
    sections: [],
    extracted_signals: [
      {
        key: "pod_candidate",
        label: "Potential POD candidate",
        value: "NOAEL candidate at 50 mg/kg/day",
        source_section_key: "abstract",
        confidence: "high",
      },
      {
        key: "exposure_signal",
        label: "Exposure signal",
        value: "Systemic exposure was monitored.",
        source_section_key: "abstract",
        confidence: "medium",
      },
      {
        key: "study_model",
        label: "Study model",
        value: "Human / clinical",
        source_section_key: "publication_types",
        confidence: "medium",
      },
      {
        key: "toxicology_takeaway",
        label: "Toxicology takeaway",
        value: "Dose context and explicit POD language were both identified.",
        source_section_key: "abstract",
        confidence: "high",
      },
    ],
    review_cue: {
      title: "Literature-backed evidence review",
      description: "Review the live article.",
    },
    retrieval_mode: "live",
    retrieved_at: "2026-05-08T12:00:00Z",
  });

  assert.equal(rows[0].label, "Potential POD candidate");
  assert.match(rows[0].value, /NOAEL candidate/);
  assert.equal(rows[3].label, "Route context");
  assert.equal(rows[3].value, "ORAL");
  assert.equal(rows[5].label, "Curation takeaway");
});
