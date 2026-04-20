"use client";

import { useEffect, useEffectEvent, useState } from "react";

type HealthResponse = {
  status: "ok" | "degraded";
  service: string;
  version: string;
  environment: string;
  database: {
    ok: boolean;
    message: string;
    detail?: string | null;
  };
};

type StatusCardProps = {
  apiBaseUrl: string;
};

type LoadState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: HealthResponse };

export function StatusCard({ apiBaseUrl }: StatusCardProps) {
  const [loadState, setLoadState] = useState<LoadState>({ kind: "loading" });

  const loadHealth = useEffectEvent(async () => {
    setLoadState({ kind: "loading" });

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/health`, {
        cache: "no-store",
      });

      const data = (await response.json()) as HealthResponse;
      setLoadState({ kind: "ready", data });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to reach the backend.";

      setLoadState({ kind: "error", message });
    }
  });

  useEffect(() => {
    void loadHealth();
  }, [apiBaseUrl]);

  if (loadState.kind === "loading") {
    return (
      <aside className="panel">
        <span className="status-pill loading">Checking stack</span>
        <h2>Waiting on backend telemetry</h2>
        <p className="subtle">
          The frontend is ready. The card is polling the FastAPI health endpoint
          for live application and database status.
        </p>
      </aside>
    );
  }

  if (loadState.kind === "error") {
    return (
      <aside className="panel">
        <span className="status-pill degraded">Backend unreachable</span>
        <h2>Frontend is up, API still missing.</h2>
        <p className="subtle">{loadState.message}</p>
        <button className="refresh-button" onClick={() => void loadHealth()}>
          Retry health check
        </button>
      </aside>
    );
  }

  const { data } = loadState;

  return (
    <aside className="panel">
      <span className={`status-pill ${data.status === "ok" ? "" : "degraded"}`}>
        {data.status === "ok" ? "Backend healthy" : "Backend degraded"}
      </span>
      <h2>{data.service}</h2>
      <div className="status-meta">
        <div className="meta-row">
          <span className="meta-label">Version</span>
          <span className="mono">{data.version}</span>
        </div>
        <div className="meta-row">
          <span className="meta-label">Environment</span>
          <span className="mono">{data.environment}</span>
        </div>
        <div className="meta-row">
          <span className="meta-label">Database</span>
          <span className="mono">{data.database.message}</span>
        </div>
        {data.database.detail ? (
          <div className="meta-row">
            <span className="meta-label">Detail</span>
            <span className="mono">{data.database.detail}</span>
          </div>
        ) : null}
      </div>
      <button className="refresh-button" onClick={() => void loadHealth()}>
        Refresh status
      </button>
    </aside>
  );
}
