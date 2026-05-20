import type { ReactNode } from "react";

import { WorkspaceNav } from "@/components/workspace-nav";
import { appConfig } from "@/lib/config";

export default function WorkspaceLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <div
      className={`workspace-shell ${appConfig.publicDemoMode ? "public-demo-shell" : ""}`}
    >
      <WorkspaceNav />
      <main
        className={`workspace-main ${appConfig.publicDemoMode ? "public-demo-main" : ""}`}
      >
        {children}
      </main>
    </div>
  );
}
