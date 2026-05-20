"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { appConfig } from "@/lib/config";
import { workspaceNavItems } from "@/lib/navigation";

export function WorkspaceNav() {
  const pathname = usePathname();
  const navItems = appConfig.publicDemoMode
    ? workspaceNavItems.filter(
        (item) => item.href === "/search" || item.href === "/saved-workspaces",
      )
    : workspaceNavItems;

  const renderedNavItems = navItems.map((item) => {
    const isActive =
      pathname === item.href ||
      (item.href === "/search" &&
        (pathname === "/molecule" || pathname === "/workspace"));

    return (
      <Link
        key={item.href}
        href={item.href}
        className={`nav-item ${isActive ? "active" : ""}`}
      >
        <div>
          <div className="nav-title">{item.label}</div>
          <div className="nav-copy">{item.description}</div>
        </div>
        <span className="nav-meta">{item.shortLabel}</span>
      </Link>
    );
  });

  if (appConfig.publicDemoMode) {
    return (
      <aside className="workspace-sidebar workspace-sidebar-public">
        <div className="public-nav-shell">
          <div className="brand-card brand-card-public">
            <div className="brand-card-main">
              <div className="brand-mark-wrap">
                <div className="brand-mark">RT</div>
              </div>
              <div>
                <div className="brand-eyebrow">Public prototype</div>
                <div className="brand-title">{appConfig.name}</div>
                <p className="brand-copy">
                  Evidence, POD, and Risk Support for Nonclinical Safety
                </p>
                <div className="brand-status-row">
                  <span className="brand-status">Live source retrieval</span>
                  <span className="brand-status subdued">Structured review surface</span>
                </div>
              </div>
            </div>

            <div className="public-nav-pills">
              {renderedNavItems}
            </div>
          </div>

          <div className="public-meta-grid">
            <div className="sidebar-note">
              <div className="sidebar-note-label">Developer</div>
              <div className="nav-copy">
                Developed by Subhajit Roy, a final-year Toxicology PhD candidate at UC Irvine.
              </div>
            </div>
            <div className="sidebar-note">
              <div className="sidebar-note-label">Contact</div>
              <a className="nav-copy" href="mailto:subhajr@uci.edu">
                subhajr@uci.edu
              </a>
            </div>
            <div className="sidebar-note">
              <div className="sidebar-note-label">Prototype mode</div>
              <div className="nav-copy">
                Search-first public demo with live source lookup and saved review snapshots.
              </div>
            </div>
          </div>
        </div>
      </aside>
    );
  }

  return (
    <aside className="workspace-sidebar">
      <div className="brand-card">
        <div className="brand-mark-wrap">
          <div className="brand-mark">RT</div>
        </div>
        <div>
          <div className="brand-eyebrow">Reviewer workspace</div>
          <div className="brand-title">{appConfig.name}</div>
          <p className="brand-copy">
            Evidence, POD, and Risk Support for Nonclinical Safety
          </p>
          <div className="brand-status-row">
            <span className="brand-status">Live source retrieval</span>
            <span className="brand-status subdued">Structured review surface</span>
          </div>
        </div>
      </div>

      <nav className="nav-stack" aria-label="Primary">
        {renderedNavItems}
      </nav>

      <div className="sidebar-note">
        <div className="sidebar-note-label">Backend</div>
        <code>{appConfig.apiBaseUrl}</code>
      </div>
    </aside>
  );
}
