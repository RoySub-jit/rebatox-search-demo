import type { ReactNode } from "react";

import { WorkspaceNav } from "@/components/workspace-nav";

export default function WorkspaceLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <div className="workspace-shell">
      <WorkspaceNav />
      <main className="workspace-main">{children}</main>
    </div>
  );
}
