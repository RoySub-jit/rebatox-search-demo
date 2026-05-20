import Link from "next/link";

import type { SearchEntityType } from "@/lib/api";
import { SEARCH_MODE_CONFIGS } from "@/lib/live-workspace";

type SearchModeSwitcherProps = {
  currentMode: SearchEntityType;
  currentQuery: string;
};

export function SearchModeSwitcher({
  currentMode,
  currentQuery,
}: SearchModeSwitcherProps) {
  return (
    <div className="search-mode-switcher" role="tablist" aria-label="Search entity type">
      {SEARCH_MODE_CONFIGS.map((mode) => {
        const href = currentQuery
          ? `/search?entity_type=${mode.value}&q=${encodeURIComponent(currentQuery)}`
          : `/search?entity_type=${mode.value}`;

        return (
          <Link
            key={mode.value}
            href={href}
            className={`search-mode-chip ${mode.value === currentMode ? "active" : ""}`}
            role="tab"
            aria-selected={mode.value === currentMode}
          >
            <span className="search-mode-chip-title">{mode.label}</span>
            <span className="search-mode-chip-copy">{mode.description}</span>
          </Link>
        );
      })}
    </div>
  );
}
