export const workspaceNavItems = [
  {
    href: "/search",
    label: "Live search",
    shortLabel: "00",
    description: "Search molecules, degradants, and E&L topics from live public sources.",
  },
  {
    href: "/saved-workspaces",
    label: "Saved workspaces",
    shortLabel: "01",
    description: "Reopen saved live-review snapshots with their original source context.",
  },
  {
    href: "/product-overview",
    label: "Product overview",
    shortLabel: "02",
    description: "Program snapshot, comparators, and readiness metrics.",
  },
  {
    href: "/calculations",
    label: "Calculations",
    shortLabel: "03",
    description: "Run backend-connected deterministic calculators.",
  },
  {
    href: "/evidence",
    label: "Evidence",
    shortLabel: "04",
    description: "Trace studies, findings, and citation spans.",
  },
  {
    href: "/review",
    label: "Review",
    shortLabel: "05",
    description: "Align expert reviewers and open review tasks.",
  },
  {
    href: "/report",
    label: "Report review",
    shortLabel: "06",
    description: "Review the full tox report with evidence, scoring, and audit trails.",
  },
] as const;
