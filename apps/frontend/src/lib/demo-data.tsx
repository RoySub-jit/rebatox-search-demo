import { StatusBadge } from "@/components/status-badge";
import type { BadgeTone } from "@/components/status-badge";
import type { CitationRecord } from "@/components/citation-panel";

export const productSnapshot = {
  name: "Cardiovex XR",
  summary:
    "A once-daily formulation advancing through evidence consolidation, quantitative safety framing, and final cross-functional review before report issuance.",
  stage: "Pre-decision",
  regulatoryTrack: "Signal qualification",
  owner: "Safety Strategy",
};

export const productMetrics = [
  {
    label: "Open evidence gaps",
    value: "03",
    hint: "Two citation spans still need reviewer confirmation and one study needs comparator normalization.",
    tone: "warning" as BadgeTone,
  },
  {
    label: "Studies in active package",
    value: "08",
    hint: "Across randomized, extension, and nonclinical bridging material.",
    tone: "success" as BadgeTone,
  },
  {
    label: "Latest MOE signal",
    value: "50x",
    hint: "Most recent deterministic margin based on the current lead exposure scenario.",
    tone: "info" as BadgeTone,
  },
  {
    label: "Review readiness",
    value: "82%",
    hint: "Calculated from completed review packets, open actions, and report section maturity.",
    tone: "neutral" as BadgeTone,
  },
] as const;

export const productHighlights = [
  {
    title: "Exposure narrative is stable",
    badge: "Locked",
    tone: "success" as BadgeTone,
    body: "The current exposure story is consistent across the clinical and manufacturing packages, with only one alternate scenario still under sensitivity review.",
  },
  {
    title: "Comparator framing needs a final cut",
    badge: "Needs choice",
    tone: "warning" as BadgeTone,
    body: "The narrative currently carries three comparator arms, but the report team only wants to foreground the two that materially change the recommendation posture.",
  },
  {
    title: "Reviewer confidence is trending up",
    badge: "Positive",
    tone: "info" as BadgeTone,
    body: "Expert review comments shifted from methodology concerns to wording and traceability, which is a better place to be late in the cycle.",
  },
] as const;

export const comparatorRows = [
  {
    id: "cmp-1",
    arm: "Cardiovex XR vs placebo",
    evidence: "Strong symptomatic improvement with aligned safety monitoring.",
    exposure: "0.4 to 0.8 mg/kg/day",
    readiness: <StatusBadge tone="success">Primary</StatusBadge>,
  },
  {
    id: "cmp-2",
    arm: "Cardiovex XR vs legacy IR",
    evidence: "Equivalent efficacy, better adherence profile, lower peak excursions.",
    exposure: "175 mg/day",
    readiness: <StatusBadge tone="info">Secondary</StatusBadge>,
  },
  {
    id: "cmp-3",
    arm: "Nonclinical bridge arm",
    evidence: "Supports POD framing but still needs narrative simplification.",
    exposure: "PDE shell only",
    readiness: <StatusBadge tone="warning">In review</StatusBadge>,
  },
];

export const productMilestones = [
  {
    id: "m-1",
    phase: "Evidence harmonization",
    owner: "Clinical Sciences",
    status: <StatusBadge tone="success">Complete</StatusBadge>,
    eta: "Delivered",
  },
  {
    id: "m-2",
    phase: "Deterministic calculation pack",
    owner: "Quant Safety",
    status: <StatusBadge tone="info">Active</StatusBadge>,
    eta: "This week",
  },
  {
    id: "m-3",
    phase: "Cross-functional review",
    owner: "Safety Strategy",
    status: <StatusBadge tone="warning">Open items</StatusBadge>,
    eta: "Next Tuesday",
  },
  {
    id: "m-4",
    phase: "Decision memo release",
    owner: "Program Lead",
    status: <StatusBadge tone="neutral">Queued</StatusBadge>,
    eta: "May 06",
  },
];

export const evidenceMetrics = [
  {
    label: "Mapped source documents",
    value: "11",
    hint: "All current studies and expert packets now point back to source material.",
    tone: "success" as BadgeTone,
  },
  {
    label: "Quoted citation spans",
    value: "24",
    hint: "Structured spans are available for the most decision-relevant excerpts.",
    tone: "info" as BadgeTone,
  },
  {
    label: "Pending adjudications",
    value: "02",
    hint: "Both are wording-level disagreements rather than substantive data disputes.",
    tone: "warning" as BadgeTone,
  },
  {
    label: "Coverage confidence",
    value: "High",
    hint: "Enough evidence has been mapped for report drafting and review packets.",
    tone: "neutral" as BadgeTone,
  },
] as const;

export const evidenceRows = [
  {
    id: "e-1",
    study: "CVX-301",
    design: "Randomized Phase II",
    finding: "Improved symptom control with stable exposure profile.",
    confidence: <StatusBadge tone="success">High</StatusBadge>,
  },
  {
    id: "e-2",
    study: "CVX-402",
    design: "Open-label extension",
    finding: "Adherence gains without new safety flags.",
    confidence: <StatusBadge tone="info">Medium-high</StatusBadge>,
  },
  {
    id: "e-3",
    study: "Tox Bridge 17A",
    design: "Nonclinical bridge",
    finding: "Supports current POD range but drives one report caveat.",
    confidence: <StatusBadge tone="warning">Medium</StatusBadge>,
  },
];

export const sourceDocumentRows = [
  {
    id: "d-1",
    document: "CSR CVX-301",
    type: "Clinical study report",
    coverage: "6 findings / 12 spans",
    status: <StatusBadge tone="success">Complete</StatusBadge>,
  },
  {
    id: "d-2",
    document: "Integrated tox summary",
    type: "Toxicology summary",
    coverage: "2 findings / 5 spans",
    status: <StatusBadge tone="info">Annotated</StatusBadge>,
  },
  {
    id: "d-3",
    document: "Reviewer memo draft",
    type: "Expert review packet",
    coverage: "3 comments / 7 spans",
    status: <StatusBadge tone="warning">Pending sign-off</StatusBadge>,
  },
];

export const evidenceCitations: CitationRecord[] = [
  {
    id: "c-1",
    title: "Exposure stability in CVX-301",
    source: "CSR CVX-301",
    pages: "Pages 88 to 89",
    label: "Primary evidence",
    tone: "success",
    excerpt:
      "Across the maintenance window, mean exposure remained within the predefined variability band and did not trigger dose-limiting observation thresholds.",
    interpretation:
      "This excerpt anchors the product overview and supports using the study as the lead evidence source for deterministic conversion examples.",
  },
  {
    id: "c-2",
    title: "Comparator adherence signal",
    source: "Extension summary",
    pages: "Pages 14 to 15",
    label: "Narrative support",
    tone: "info",
    excerpt:
      "Patients transitioning from the immediate-release comparator demonstrated fewer missed daily administrations over the first 12 weeks of the extension period.",
    interpretation:
      "The review and report pages use this to justify why the IR comparator remains in the final narrative despite not being the headline efficacy comparison.",
  },
  {
    id: "c-3",
    title: "POD caution language",
    source: "Integrated tox summary",
    pages: "Pages 41 to 42",
    label: "Needs caveat",
    tone: "warning",
    excerpt:
      "The selected point of departure is appropriate for quantitative screening; however, interpretation should note the limited duration bridge and database completeness caveat.",
    interpretation:
      "This is the basis for the report-side caveat and the review team’s remaining wording discussion.",
  },
];

export const reviewMetrics = [
  {
    label: "Lead reviewers aligned",
    value: "2 / 3",
    hint: "Clinical and regulatory are aligned; tox requests one caveat tweak.",
    tone: "success" as BadgeTone,
  },
  {
    label: "Open review tasks",
    value: "04",
    hint: "Only one is blocking final report freeze.",
    tone: "warning" as BadgeTone,
  },
  {
    label: "Mean expert score",
    value: "4.4 / 5",
    hint: "Captured across the latest expert review packet revisions.",
    tone: "info" as BadgeTone,
  },
  {
    label: "Decision confidence",
    value: "Moderate-high",
    hint: "Strong enough for draft release, with one wording contingency.",
    tone: "neutral" as BadgeTone,
  },
] as const;

export const reviewRows = [
  {
    id: "r-1",
    item: "Lead quantitative framing",
    owner: "Clinical Safety",
    decision: <StatusBadge tone="success">Accept</StatusBadge>,
    date: "Today",
  },
  {
    id: "r-2",
    item: "POD caveat wording",
    owner: "Toxicology",
    decision: <StatusBadge tone="warning">Revise</StatusBadge>,
    date: "Yesterday",
  },
  {
    id: "r-3",
    item: "Comparator prominence",
    owner: "Regulatory Affairs",
    decision: <StatusBadge tone="info">Conditional</StatusBadge>,
    date: "Today",
  },
];

export const reviewTasks = [
  {
    title: "Confirm final caveat sentence for the PDE/ADE narrative",
    badge: "Blocker",
    tone: "danger" as BadgeTone,
    body: "Toxicology wants a single sentence in the report to make the duration bridge limitation explicit without weakening the primary recommendation.",
  },
  {
    title: "Lock the comparator appendix ordering",
    badge: "Active",
    tone: "warning" as BadgeTone,
    body: "Regulatory wants the IR comparator appendix retained, but moved behind the primary placebo comparison in the final packet.",
  },
  {
    title: "Final reviewer packet export",
    badge: "Ready",
    tone: "success" as BadgeTone,
    body: "Once the caveat is settled, the packet is otherwise ready for distribution.",
  },
];

export const reviewCitations: CitationRecord[] = [
  {
    id: "rc-1",
    title: "Reviewer note on POD framing",
    source: "Expert review memo",
    pages: "Comment block 12",
    label: "Open comment",
    tone: "warning",
    excerpt:
      "I am comfortable with the selected POD for screening purposes, but the current language understates the duration limitation in the supporting bridge evidence.",
    interpretation:
      "This is the single blocking comment keeping the review page from a full green status.",
  },
  {
    id: "rc-2",
    title: "Clinical lead support statement",
    source: "Clinical sign-off draft",
    pages: "Paragraph 3",
    label: "Aligned",
    tone: "success",
    excerpt:
      "The benefit-risk framing is coherent, and the supporting evidence package is sufficient for the current draft recommendation.",
    interpretation:
      "This comment supports moving the report into near-final authoring while the tox wording is still being tuned.",
  },
];

export const reportMetrics = [
  {
    label: "Sections draft-complete",
    value: "6 / 8",
    hint: "Only the limitations and appendix summary still need final edits.",
    tone: "info" as BadgeTone,
  },
  {
    label: "Claims fully cited",
    value: "12",
    hint: "Every decision-relevant claim now has at least one expandable citation panel.",
    tone: "success" as BadgeTone,
  },
  {
    label: "Outstanding edits",
    value: "05",
    hint: "Mostly wording polish and one appendix ordering change.",
    tone: "warning" as BadgeTone,
  },
  {
    label: "Report confidence",
    value: "Release candidate",
    hint: "Once the final caveat lands, the memo is ready to freeze.",
    tone: "neutral" as BadgeTone,
  },
] as const;

export const reportSections = [
  {
    id: "s-1",
    section: "Executive summary",
    owner: "Program Lead",
    status: <StatusBadge tone="success">Approved</StatusBadge>,
    lastEdited: "Today",
  },
  {
    id: "s-2",
    section: "Evidence synthesis",
    owner: "Clinical Sciences",
    status: <StatusBadge tone="success">Approved</StatusBadge>,
    lastEdited: "Today",
  },
  {
    id: "s-3",
    section: "Quantitative calculations",
    owner: "Quant Safety",
    status: <StatusBadge tone="info">Live</StatusBadge>,
    lastEdited: "Today",
  },
  {
    id: "s-4",
    section: "Limitations and caveats",
    owner: "Toxicology",
    status: <StatusBadge tone="warning">Needs edit</StatusBadge>,
    lastEdited: "Yesterday",
  },
];

export const reportRows = [
  {
    id: "rr-1",
    claim: "Exposure remains within the accepted operating band in the lead study package.",
    strength: <StatusBadge tone="success">Strong</StatusBadge>,
    source: "CSR CVX-301",
    state: <StatusBadge tone="success">Ready</StatusBadge>,
  },
  {
    id: "rr-2",
    claim: "The PDE/ADE shell supports screening-level decision framing when caveated appropriately.",
    strength: <StatusBadge tone="warning">Qualified</StatusBadge>,
    source: "Integrated tox summary",
    state: <StatusBadge tone="warning">Needs caveat</StatusBadge>,
  },
  {
    id: "rr-3",
    claim: "Comparator adherence performance strengthens the once-daily narrative.",
    strength: <StatusBadge tone="info">Moderate</StatusBadge>,
    source: "Extension summary",
    state: <StatusBadge tone="info">Appendix link</StatusBadge>,
  },
];

export const reportCitations: CitationRecord[] = [
  {
    id: "rp-1",
    title: "Lead exposure claim",
    source: "CSR CVX-301",
    pages: "Pages 88 to 89",
    label: "Executive summary",
    tone: "success",
    excerpt:
      "Mean exposure remained within the predefined variability band and did not trigger dose-limiting observation thresholds.",
    interpretation:
      "This is the primary quoted support for the report’s headline safety consistency claim.",
  },
  {
    id: "rp-2",
    title: "Qualified PDE/ADE statement",
    source: "Integrated tox summary",
    pages: "Pages 41 to 42",
    label: "Caveat required",
    tone: "warning",
    excerpt:
      "The selected point of departure is appropriate for quantitative screening; however, interpretation should note the limited duration bridge and database completeness caveat.",
    interpretation:
      "This citation is attached to the caveat-heavy report section and explains why the wording remains under toxicology review.",
  },
];
