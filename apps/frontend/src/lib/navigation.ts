export const workspaceNavItems = [
  {
    href: "/search",
    label: "Molecule search",
    shortLabel: "00",
    description: "Search live label metadata by brand, generic, or substance name.",
  },
  {
    href: "/product-overview",
    label: "Product overview",
    shortLabel: "01",
    description: "Program snapshot, comparators, and readiness metrics.",
  },
  {
    href: "/calculations",
    label: "Calculations",
    shortLabel: "02",
    description: "Run backend-connected deterministic calculators.",
  },
  {
    href: "/evidence",
    label: "Evidence",
    shortLabel: "03",
    description: "Trace studies, findings, and citation spans.",
  },
  {
    href: "/review",
    label: "Review",
    shortLabel: "04",
    description: "Align expert reviewers and open review tasks.",
  },
  {
    href: "/report",
    label: "Report review",
    shortLabel: "05",
    description: "Review the full tox report with evidence, scoring, and audit trails.",
  },
] as const;
