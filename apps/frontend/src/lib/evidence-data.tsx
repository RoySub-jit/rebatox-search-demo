import { ConfidenceBadge, type ConfidenceLevel } from "@/components/confidence-badge";
import { SourceTypeBadge, type SourceType } from "@/components/source-type-badge";
import { StatusBadge } from "@/components/status-badge";
import type { CitationRecord } from "@/components/citation-panel";
import type { BadgeTone } from "@/components/status-badge";

type ExtractedStudyFieldRecord = {
  label: string;
  value: string;
  citation: string;
};

export type ExtractedStudyDetailRecord = {
  id: string;
  title: string;
  summary: string;
  sourceDocument: string;
  sourceType: SourceType;
  confidence: ConfidenceLevel;
  coverageLabel: string;
  fields: ExtractedStudyFieldRecord[];
};

export const evidenceMetrics = [
  {
    label: "Source documents in scope",
    value: "11",
    hint: "Clinical reports, tox summaries, literature packages, and reviewer packets are all indexed to the same evidence view.",
    tone: "success" as BadgeTone,
  },
  {
    label: "Extracted study fields",
    value: "27",
    hint: "Structured extraction spans species, route, duration, dose, exposure, study type, and explicit POD mentions.",
    tone: "info" as BadgeTone,
  },
  {
    label: "Candidate PODs under review",
    value: "03",
    hint: "One lead POD, one bridge-dependent fallback, and one literature-backed comparator candidate remain visible.",
    tone: "warning" as BadgeTone,
  },
  {
    label: "Traceability confidence",
    value: "High",
    hint: "Every decision-facing row below links back to a source document and a citation drill-down panel.",
    tone: "neutral" as BadgeTone,
  },
] as const;

export const sourceDocumentRows = [
  {
    id: "doc-1",
    document: (
      <div className="table-copy">
        <strong>CSR CVX-301</strong>
        <span className="table-subcopy">
          Lead oral maintenance study packet with the most complete dose and exposure mapping.
        </span>
      </div>
    ),
    sourceType: <SourceTypeBadge sourceType="clinical" />,
    coverage: (
      <div className="table-copy">
        <strong>2 extracted studies</strong>
        <span className="table-subcopy">12 citation spans across route, duration, exposure, and findings.</span>
      </div>
    ),
    confidence: <ConfidenceBadge level="high" />,
    status: <StatusBadge tone="success">Indexed</StatusBadge>,
  },
  {
    id: "doc-2",
    document: (
      <div className="table-copy">
        <strong>Tox Bridge 17A</strong>
        <span className="table-subcopy">
          Nonclinical bridge report carrying the current explicit NOAEL and LOAEL support.
        </span>
      </div>
    ),
    sourceType: <SourceTypeBadge sourceType="nonclinical" />,
    coverage: (
      <div className="table-copy">
        <strong>1 extracted study</strong>
        <span className="table-subcopy">8 citation spans tied to species, route, dose band, and POD mentions.</span>
      </div>
    ),
    confidence: <ConfidenceBadge level="medium-high" />,
    status: <StatusBadge tone="info">Mapped</StatusBadge>,
  },
  {
    id: "doc-3",
    document: (
      <div className="table-copy">
        <strong>PubMed Bridge Review</strong>
        <span className="table-subcopy">
          Literature summary used to frame analog evidence and exposure comparability.
        </span>
      </div>
    ),
    sourceType: <SourceTypeBadge sourceType="literature" />,
    coverage: (
      <div className="table-copy">
        <strong>1 extracted study note</strong>
        <span className="table-subcopy">4 citation spans supporting analog-only and comparator context.</span>
      </div>
    ),
    confidence: <ConfidenceBadge level="medium" />,
    status: <StatusBadge tone="warning">Needs adjudication</StatusBadge>,
  },
  {
    id: "doc-4",
    document: (
      <div className="table-copy">
        <strong>Expert Review Packet Draft</strong>
        <span className="table-subcopy">
          Reviewer-facing synthesis with wording comments on the bridge-dependent POD narrative.
        </span>
      </div>
    ),
    sourceType: <SourceTypeBadge sourceType="review" />,
    coverage: (
      <div className="table-copy">
        <strong>3 linked findings</strong>
        <span className="table-subcopy">7 spans linked to finding confidence and final report caveats.</span>
      </div>
    ),
    confidence: <ConfidenceBadge level="review" />,
    status: <StatusBadge tone="neutral">In packet prep</StatusBadge>,
  },
];

export const extractedStudyDetails: ExtractedStudyDetailRecord[] = [
  {
    id: "study-1",
    title: "CVX-301 maintenance cohort",
    summary:
      "Rule-based extraction cleanly captured the clinical route, duration, and exposure framing from the lead maintenance package.",
    sourceDocument: "CSR CVX-301",
    sourceType: "clinical",
    confidence: "high",
    coverageLabel: "6 cited fields",
    fields: [
      {
        label: "Species / population",
        value: "Adult human maintenance cohort",
        citation: "CSR CVX-301 · Chunk 04 · Pages 21 to 22",
      },
      {
        label: "Route",
        value: "Oral once-daily administration",
        citation: "CSR CVX-301 · Chunk 05 · Page 23",
      },
      {
        label: "Duration",
        value: "12-week treatment window",
        citation: "CSR CVX-301 · Chunk 06 · Page 24",
      },
      {
        label: "Dose text",
        value: "175 mg/day maintenance regimen",
        citation: "CSR CVX-301 · Chunk 08 · Page 27",
      },
      {
        label: "Exposure text",
        value: "Systemic exposure remained within the predefined variability band.",
        citation: "CSR CVX-301 · Chunk 18 · Pages 88 to 89",
      },
      {
        label: "Study type",
        value: "Randomized clinical trial",
        citation: "CSR CVX-301 · Chunk 03 · Page 20",
      },
    ],
  },
  {
    id: "study-2",
    title: "Tox Bridge 17A repeat-dose package",
    summary:
      "The bridge study has the strongest explicit POD language and carries the clearest species and dose-series extraction footprint.",
    sourceDocument: "Tox Bridge 17A",
    sourceType: "nonclinical",
    confidence: "medium-high",
    coverageLabel: "7 cited fields",
    fields: [
      {
        label: "Species / population",
        value: "Sprague-Dawley rat",
        citation: "Tox Bridge 17A · Chunk 02 · Page 9",
      },
      {
        label: "Route",
        value: "Oral gavage",
        citation: "Tox Bridge 17A · Chunk 03 · Page 10",
      },
      {
        label: "Duration",
        value: "28-day repeat-dose schedule",
        citation: "Tox Bridge 17A · Chunk 03 · Page 10",
      },
      {
        label: "Dose text",
        value: "5, 15, and 45 mg/kg/day dose series",
        citation: "Tox Bridge 17A · Chunk 04 · Page 11",
      },
      {
        label: "Exposure text",
        value: "Systemic exposure (AUC0-24) increased proportionally with dose.",
        citation: "Tox Bridge 17A · Chunk 07 · Pages 14 to 15",
      },
      {
        label: "Study type",
        value: "Repeat-dose toxicology study",
        citation: "Tox Bridge 17A · Chunk 02 · Page 9",
      },
      {
        label: "Explicit POD mentions",
        value: "NOAEL 5 mg/kg/day and LOAEL 15 mg/kg/day",
        citation: "Tox Bridge 17A · Chunk 09 · Pages 18 to 19",
      },
    ],
  },
  {
    id: "study-3",
    title: "Comparator literature bridge review",
    summary:
      "Literature extraction is usable, but it still carries analog-heavy support and a looser exposure narrative than the lead clinical and tox documents.",
    sourceDocument: "PubMed Bridge Review",
    sourceType: "literature",
    confidence: "medium",
    coverageLabel: "5 cited fields",
    fields: [
      {
        label: "Species / population",
        value: "Adult patient case series",
        citation: "PubMed Bridge Review · Chunk 01 · Page 1",
      },
      {
        label: "Route",
        value: "Oral comparator dosing",
        citation: "PubMed Bridge Review · Chunk 02 · Page 2",
      },
      {
        label: "Duration",
        value: "8-week follow-up window",
        citation: "PubMed Bridge Review · Chunk 02 · Page 2",
      },
      {
        label: "Exposure text",
        value: "Comparator exposure remained directionally aligned with the bridge estimate.",
        citation: "PubMed Bridge Review · Chunk 05 · Page 4",
      },
      {
        label: "Study type",
        value: "Cohort study",
        citation: "PubMed Bridge Review · Chunk 01 · Page 1",
      },
    ],
  },
];

export const findingRows = [
  {
    id: "finding-1",
    finding: (
      <div className="table-copy">
        <strong>Exposure stability remained inside the maintenance operating band.</strong>
        <span className="table-subcopy">Used as the lead safety consistency claim in the draft report.</span>
      </div>
    ),
    supportingStudy: (
      <div className="table-copy">
        <strong>CVX-301 maintenance cohort</strong>
        <span className="table-subcopy">CSR CVX-301 · exposure + duration extraction both aligned.</span>
      </div>
    ),
    confidence: <ConfidenceBadge level="high" />,
    status: <StatusBadge tone="success">Report-ready</StatusBadge>,
  },
  {
    id: "finding-2",
    finding: (
      <div className="table-copy">
        <strong>The bridge tox package supports a defensible quantitative screen.</strong>
        <span className="table-subcopy">Relies on explicit NOAEL / LOAEL extraction and species relevance language.</span>
      </div>
    ),
    supportingStudy: (
      <div className="table-copy">
        <strong>Tox Bridge 17A</strong>
        <span className="table-subcopy">Dose series, oral gavage route, and POD mentions all cite cleanly.</span>
      </div>
    ),
    confidence: <ConfidenceBadge level="medium-high" />,
    status: <StatusBadge tone="info">Caveat retained</StatusBadge>,
  },
  {
    id: "finding-3",
    finding: (
      <div className="table-copy">
        <strong>Comparator adherence still helps the once-daily narrative.</strong>
        <span className="table-subcopy">Literature support exists, but it is weaker and more analog-shaped than the primary package.</span>
      </div>
    ),
    supportingStudy: (
      <div className="table-copy">
        <strong>PubMed Bridge Review</strong>
        <span className="table-subcopy">Best treated as contextual support rather than a lead evidence anchor.</span>
      </div>
    ),
    confidence: <ConfidenceBadge level="medium" />,
    status: <StatusBadge tone="warning">Secondary support</StatusBadge>,
  },
];

export const candidatePodRows = [
  {
    id: "pod-1",
    candidate: (
      <div className="table-copy">
        <strong>Lead NOAEL candidate</strong>
        <span className="table-subcopy">5 mg/kg/day from the repeat-dose bridge package.</span>
      </div>
    ),
    basis: (
      <div className="table-copy">
        <strong>Explicit POD mention + aligned route</strong>
        <span className="table-subcopy">Species, route, duration, and dose series all trace back to the same source document.</span>
      </div>
    ),
    caveat: "Requires final wording on duration-bridge limitations.",
    confidence: <ConfidenceBadge level="high" />,
    status: <StatusBadge tone="success">Primary candidate</StatusBadge>,
  },
  {
    id: "pod-2",
    candidate: (
      <div className="table-copy">
        <strong>Comparator-support fallback</strong>
        <span className="table-subcopy">175 mg/day clinical regimen retained for framing, not as the lead POD.</span>
      </div>
    ),
    basis: (
      <div className="table-copy">
        <strong>Clinical route and exposure extraction are strong</strong>
        <span className="table-subcopy">No explicit POD in the clinical text, so this remains supportive rather than primary.</span>
      </div>
    ),
    caveat: "Needs explicit note that the clinical packet does not name a formal POD.",
    confidence: <ConfidenceBadge level="medium-high" />,
    status: <StatusBadge tone="info">Supportive only</StatusBadge>,
  },
  {
    id: "pod-3",
    candidate: (
      <div className="table-copy">
        <strong>Analog literature bridge</strong>
        <span className="table-subcopy">Comparator literature remains visible because it affects narrative tone, not primary quantitation.</span>
      </div>
    ),
    basis: (
      <div className="table-copy">
        <strong>Analog-only extraction footprint</strong>
        <span className="table-subcopy">Useful for discussion, but too indirect to stand alone in the final quantitative recommendation.</span>
      </div>
    ),
    caveat: "Keep as secondary support and surface the analog-only limitation explicitly.",
    confidence: <ConfidenceBadge level="medium" />,
    status: <StatusBadge tone="warning">Bridge-dependent</StatusBadge>,
  },
];

export const evidenceCitations: CitationRecord[] = [
  {
    id: "citation-1",
    title: "Clinical route and duration extraction",
    source: "CSR CVX-301",
    pages: "Chunk 05 · Pages 23 to 24",
    label: "Extracted study detail",
    tone: "info",
    sourceType: "clinical",
    confidence: "high",
    fieldLabel: "Route + duration",
    entityLabel: "CVX-301 maintenance cohort",
    excerpt:
      "Patients received oral once-daily administration for a 12-week treatment window during the maintenance phase of the trial.",
    interpretation:
      "This span anchors the extracted route and duration fields used in the evidence workspace and keeps the clinical regimen comparable to downstream calculations.",
  },
  {
    id: "citation-2",
    title: "Nonclinical dose series and POD mention",
    source: "Tox Bridge 17A",
    pages: "Chunk 09 · Pages 18 to 19",
    label: "Candidate POD support",
    tone: "success",
    sourceType: "nonclinical",
    confidence: "medium-high",
    fieldLabel: "Dose text + explicit POD",
    entityLabel: "Lead NOAEL candidate",
    excerpt:
      "A NOAEL of 5 mg/kg/day was identified, while findings at 15 mg/kg/day established the corresponding LOAEL under the oral gavage schedule.",
    interpretation:
      "This is the strongest single citation for the lead candidate POD because it ties the dose series, route, and explicit POD statement together.",
  },
  {
    id: "citation-3",
    title: "Exposure proportionality signal",
    source: "Tox Bridge 17A",
    pages: "Chunk 07 · Pages 14 to 15",
    label: "Finding support",
    tone: "info",
    sourceType: "nonclinical",
    confidence: "medium-high",
    fieldLabel: "Exposure text",
    entityLabel: "Bridge tox quantitative finding",
    excerpt:
      "Systemic exposure (AUC0-24) increased proportionally with dose across the 5, 15, and 45 mg/kg/day cohorts.",
    interpretation:
      "This is why the tox bridge study remains useful for deterministic screening even though it still needs a bridge-specific report caveat.",
  },
  {
    id: "citation-4",
    title: "Analog-only literature framing",
    source: "PubMed Bridge Review",
    pages: "Chunk 05 · Page 4",
    label: "Context only",
    tone: "warning",
    sourceType: "literature",
    confidence: "medium",
    fieldLabel: "Analog evidence",
    entityLabel: "Comparator-support fallback",
    excerpt:
      "Comparator exposure remained directionally aligned with the bridge estimate, although the discussion relies on an analog support package rather than direct product-specific dosing evidence.",
    interpretation:
      "This drill-down explains why the literature-backed candidate stays visible in the page while still being framed as secondary support.",
  },
  {
    id: "citation-5",
    title: "Reviewer caveat on bridge dependence",
    source: "Expert Review Packet Draft",
    pages: "Comment block 12",
    label: "Review comment",
    tone: "warning",
    sourceType: "review",
    confidence: "review",
    fieldLabel: "Limitation wording",
    entityLabel: "Lead NOAEL candidate",
    excerpt:
      "The selected point of departure is acceptable for screening-level decision support, but the narrative should make the duration bridge caveat explicit in the final recommendation.",
    interpretation:
      "This reviewer citation is the main reason the evidence page keeps the lead POD at high confidence while still surfacing an active caveat badge elsewhere.",
  },
];
