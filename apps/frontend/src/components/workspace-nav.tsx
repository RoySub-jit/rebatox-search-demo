"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { appConfig } from "@/lib/config";
import { workspaceNavItems } from "@/lib/navigation";

export function WorkspaceNav() {
  const pathname = usePathname();
  const navItems = appConfig.publicDemoMode
    ? workspaceNavItems.filter((item) => item.href === "/search")
    : workspaceNavItems;

  return (
    <aside className="workspace-sidebar">
      <div className="brand-card">
        <div className="brand-mark">RT</div>
        <div>
          <div className="brand-title">{appConfig.name}</div>
          <p className="brand-copy">
            Evidence, POD, and Risk Support for Nonclinical Safety
          </p>
        </div>
      </div>

      <nav className="nav-stack" aria-label="Primary">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href === "/search" && pathname === "/molecule");

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
        })}
      </nav>

      <div className="sidebar-note">
        <div className="sidebar-note-label">Backend</div>
        <code>{appConfig.apiBaseUrl}</code>
      </div>

      {appConfig.publicDemoMode ? (
        <div className="sidebar-note">
          <div className="sidebar-note-label">Mode</div>
          <div className="nav-copy">
            Public search demo with live source lookup. Internal report workflow is
            intentionally hidden in this hosted view.
          </div>
        </div>
      ) : null}
    </aside>
  );
}
