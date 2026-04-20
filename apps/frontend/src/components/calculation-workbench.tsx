"use client";

import {
  startTransition,
  useEffectEvent,
  useState,
} from "react";

import { StatusBadge } from "@/components/status-badge";
import {
  ApiClientError,
  getCalculationRun,
  runCalculation,
  type CalculationRunResponse,
  type CalculationType,
  type RunCalculationPayload,
} from "@/lib/api";

type CalculationWorkbenchProps = {
  apiBaseUrl: string;
};

type FieldConfig = {
  name: string;
  label: string;
  placeholder: string;
  note: string;
};

type RunConfig = {
  label: string;
  summary: string;
  fields: FieldConfig[];
  defaults: Record<string, string>;
};

const LINK_FIELD_LABELS = {
  product_id: "Product ID",
  comparator_id: "Comparator ID",
  study_id: "Study ID",
  candidate_pod_id: "Candidate POD ID",
} as const;

const RUN_CONFIGS: Record<CalculationType, RunConfig> = {
  mg_per_kg_day_to_mg_per_day: {
    label: "mg/kg/day to mg/day",
    summary: "Convert a weight-normalized daily dose into an absolute daily dose.",
    fields: [
      {
        name: "dose_mg_per_kg_day",
        label: "Dose (mg/kg/day)",
        placeholder: "2.5",
        note: "Weight-normalized daily dose.",
      },
      {
        name: "body_weight_kg",
        label: "Body weight (kg)",
        placeholder: "70",
        note: "Body weight used for conversion.",
      },
    ],
    defaults: {
      dose_mg_per_kg_day: "2.5",
      body_weight_kg: "70",
    },
  },
  mg_per_day_to_mg_per_kg_day: {
    label: "mg/day to mg/kg/day",
    summary: "Normalize a daily dose by body weight for cross-study comparison.",
    fields: [
      {
        name: "dose_mg_per_day",
        label: "Dose (mg/day)",
        placeholder: "175",
        note: "Absolute daily dose.",
      },
      {
        name: "body_weight_kg",
        label: "Body weight (kg)",
        placeholder: "70",
        note: "Body weight used for normalization.",
      },
    ],
    defaults: {
      dose_mg_per_day: "175",
      body_weight_kg: "70",
    },
  },
  margin_of_exposure: {
    label: "Margin of exposure",
    summary: "Compare the point of departure directly to an observed or modeled exposure.",
    fields: [
      {
        name: "point_of_departure",
        label: "Point of departure",
        placeholder: "100",
        note: "Use the same basis as exposure.",
      },
      {
        name: "exposure",
        label: "Exposure",
        placeholder: "2",
        note: "Exposure must be on the same basis as the POD.",
      },
      {
        name: "basis",
        label: "Basis",
        placeholder: "mg/kg/day",
        note: "Used for display and traceability.",
      },
    ],
    defaults: {
      point_of_departure: "100",
      exposure: "2",
      basis: "mg/kg/day",
    },
  },
  pde: {
    label: "PDE shell",
    summary: "Apply modifying factors to a point of departure using a 50 kg default body weight.",
    fields: [
      {
        name: "point_of_departure_mg_per_kg_day",
        label: "Point of departure (mg/kg/day)",
        placeholder: "5",
        note: "Supply the selected toxicological POD.",
      },
      {
        name: "body_weight_kg",
        label: "Body weight (kg)",
        placeholder: "50",
        note: "Regulatory default is commonly 50 kg.",
      },
      {
        name: "modifying_factor_f1",
        label: "F1",
        placeholder: "2",
        note: "Species extrapolation factor.",
      },
      {
        name: "modifying_factor_f2",
        label: "F2",
        placeholder: "5",
        note: "Inter-individual variability factor.",
      },
      {
        name: "modifying_factor_f3",
        label: "F3",
        placeholder: "10",
        note: "Duration adjustment factor.",
      },
      {
        name: "modifying_factor_f4",
        label: "F4",
        placeholder: "1",
        note: "Severity or endpoint factor.",
      },
      {
        name: "modifying_factor_f5",
        label: "F5",
        placeholder: "1",
        note: "Database uncertainty factor.",
      },
      {
        name: "point_of_departure_label",
        label: "POD label",
        placeholder: "NOAEL",
        note: "Displayed in the structured result.",
      },
      {
        name: "result_unit",
        label: "Result unit",
        placeholder: "mg/day",
        note: "Label used in the response.",
      },
    ],
    defaults: {
      point_of_departure_mg_per_kg_day: "5",
      body_weight_kg: "50",
      modifying_factor_f1: "2",
      modifying_factor_f2: "5",
      modifying_factor_f3: "10",
      modifying_factor_f4: "1",
      modifying_factor_f5: "1",
      point_of_departure_label: "NOAEL",
      result_unit: "mg/day",
    },
  },
  ade: {
    label: "ADE shell",
    summary: "Use the same structured shell with ADE labeling and adjustable factors.",
    fields: [
      {
        name: "point_of_departure_mg_per_kg_day",
        label: "Point of departure (mg/kg/day)",
        placeholder: "0.6",
        note: "Supply the selected toxicological POD.",
      },
      {
        name: "body_weight_kg",
        label: "Body weight (kg)",
        placeholder: "50",
        note: "Regulatory default is commonly 50 kg.",
      },
      {
        name: "modifying_factor_f1",
        label: "F1",
        placeholder: "1",
        note: "Species extrapolation factor.",
      },
      {
        name: "modifying_factor_f2",
        label: "F2",
        placeholder: "1",
        note: "Inter-individual variability factor.",
      },
      {
        name: "modifying_factor_f3",
        label: "F3",
        placeholder: "1",
        note: "Duration adjustment factor.",
      },
      {
        name: "modifying_factor_f4",
        label: "F4",
        placeholder: "1",
        note: "Severity or endpoint factor.",
      },
      {
        name: "modifying_factor_f5",
        label: "F5",
        placeholder: "1",
        note: "Database uncertainty factor.",
      },
      {
        name: "point_of_departure_label",
        label: "POD label",
        placeholder: "POD",
        note: "Displayed in the structured result.",
      },
      {
        name: "result_unit",
        label: "Result unit",
        placeholder: "mg/day",
        note: "Label used in the response.",
      },
    ],
    defaults: {
      point_of_departure_mg_per_kg_day: "0.6",
      body_weight_kg: "50",
      modifying_factor_f1: "1",
      modifying_factor_f2: "1",
      modifying_factor_f3: "1",
      modifying_factor_f4: "1",
      modifying_factor_f5: "1",
      point_of_departure_label: "POD",
      result_unit: "mg/day",
    },
  },
};

const CALCULATION_TYPE_ORDER = Object.keys(RUN_CONFIGS) as CalculationType[];

function createPayload(
  runType: CalculationType,
  values: Record<string, string>,
  links: Record<keyof typeof LINK_FIELD_LABELS, string>,
): RunCalculationPayload {
  const payload: RunCalculationPayload = {
    run_type: runType,
    inputs: values,
  };

  for (const [fieldName, value] of Object.entries(links)) {
    if (!value.trim()) {
      continue;
    }

    payload[fieldName as keyof typeof LINK_FIELD_LABELS] = Number(value);
  }

  return payload;
}

function describeApiError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to reach the calculation service.";
}

export function CalculationWorkbench({
  apiBaseUrl,
}: CalculationWorkbenchProps) {
  const [runType, setRunType] = useState<CalculationType>("margin_of_exposure");
  const [linkValues, setLinkValues] = useState<
    Record<keyof typeof LINK_FIELD_LABELS, string>
  >({
    product_id: "",
    comparator_id: "",
    study_id: "",
    candidate_pod_id: "",
  });
  const [fieldValues, setFieldValues] = useState<Record<string, string>>(
    RUN_CONFIGS.margin_of_exposure.defaults,
  );
  const [activeRun, setActiveRun] = useState<CalculationRunResponse | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [runId, setRunId] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isReloading, setIsReloading] = useState(false);

  const currentConfig = RUN_CONFIGS[runType];

  const payloadPreview = createPayload(runType, fieldValues, linkValues);

  const submitRun = useEffectEvent(async () => {
    setIsSubmitting(true);
    setRequestError(null);

    try {
      const response = await runCalculation(apiBaseUrl, payloadPreview);
      startTransition(() => {
        setActiveRun(response);
        setRunId(response.id);
      });
    } catch (error) {
      setRequestError(describeApiError(error));
    } finally {
      setIsSubmitting(false);
    }
  });

  const reloadRun = useEffectEvent(async () => {
    if (!runId) {
      return;
    }

    setIsReloading(true);
    setRequestError(null);

    try {
      const response = await getCalculationRun(apiBaseUrl, runId);
      startTransition(() => {
        setActiveRun(response);
      });
    } catch (error) {
      setRequestError(describeApiError(error));
    } finally {
      setIsReloading(false);
    }
  });

  return (
    <section className="calculation-grid">
      <article className="card workbench-card">
        <div className="card-heading">
          <div>
            <span className="section-kicker">Backend-connected run form</span>
            <h2>Calculation controls</h2>
          </div>
          <StatusBadge tone="info">POST + GET live</StatusBadge>
        </div>

        <div className="field">
          <label className="field-label" htmlFor="run-type">
            Calculator
          </label>
          <select
            id="run-type"
            className="input-control"
            value={runType}
            onChange={(event) => {
              const nextType = event.target.value as CalculationType;
              setRunType(nextType);
              startTransition(() => {
                setFieldValues(RUN_CONFIGS[nextType].defaults);
                setRequestError(null);
              });
            }}
          >
            {CALCULATION_TYPE_ORDER.map((type) => (
              <option key={type} value={type}>
                {RUN_CONFIGS[type].label}
              </option>
            ))}
          </select>
          <p className="field-note">{currentConfig.summary}</p>
        </div>

        <div className="field-grid">
          {(Object.entries(LINK_FIELD_LABELS) as Array<
            [keyof typeof LINK_FIELD_LABELS, string]
          >).map(([fieldName, label]) => (
            <div className="field" key={fieldName}>
              <label className="field-label" htmlFor={fieldName}>
                {label}
              </label>
              <input
                id={fieldName}
                className="input-control"
                inputMode="numeric"
                placeholder="Optional"
                value={linkValues[fieldName]}
                onChange={(event) =>
                  setLinkValues((current) => ({
                    ...current,
                    [fieldName]: event.target.value,
                  }))
                }
              />
            </div>
          ))}
        </div>

        <div className="field-grid">
          {currentConfig.fields.map((field) => (
            <div className="field" key={field.name}>
              <label className="field-label" htmlFor={field.name}>
                {field.label}
              </label>
              <input
                id={field.name}
                className="input-control"
                placeholder={field.placeholder}
                value={fieldValues[field.name] ?? ""}
                onChange={(event) =>
                  setFieldValues((current) => ({
                    ...current,
                    [field.name]: event.target.value,
                  }))
                }
              />
              <p className="field-note">{field.note}</p>
            </div>
          ))}
        </div>

        <div className="button-row">
          <button
            className="button-primary"
            disabled={isSubmitting}
            onClick={() => void submitRun()}
            type="button"
          >
            {isSubmitting ? "Running calculation..." : "Run calculation"}
          </button>
          <button
            className="button-secondary"
            disabled={!runId || isReloading}
            onClick={() => void reloadRun()}
            type="button"
          >
            {isReloading ? "Reloading..." : "Reload saved run"}
          </button>
        </div>

        {requestError ? (
          <div className="feedback-banner danger">
            <strong>Backend error</strong>
            <p>{requestError}</p>
          </div>
        ) : null}
      </article>

      <div className="results-stack">
        <article className="card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Request preview</span>
              <h2>Payload to backend</h2>
            </div>
            <StatusBadge tone="neutral">JSON</StatusBadge>
          </div>
          <pre className="code-panel">
            {JSON.stringify(payloadPreview, null, 2)}
          </pre>
        </article>

        <article className="card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Persisted result</span>
              <h2>Latest saved calculation</h2>
            </div>
            <StatusBadge tone={activeRun ? "success" : "warning"}>
              {activeRun ? `Run #${activeRun.id}` : "No run yet"}
            </StatusBadge>
          </div>

          {activeRun ? (
            <div className="result-stack">
              <div className="result-topline">
                <div>
                  <div className="metric-label">Formula</div>
                  <div className="formula-copy">{activeRun.output.formula}</div>
                </div>
                <StatusBadge
                  tone={activeRun.status === "warning" ? "warning" : "success"}
                >
                  {activeRun.status}
                </StatusBadge>
              </div>

              <div className="result-grid">
                <div className="result-card">
                  <span className="metric-label">Result</span>
                  <div className="result-value">
                    {activeRun.output.result
                      ? JSON.stringify(activeRun.output.result)
                      : "No result"}
                  </div>
                </div>
                <div className="result-card">
                  <span className="metric-label">Linked resources</span>
                  <div className="result-meta">
                    <span>Product: {activeRun.product_id ?? "—"}</span>
                    <span>Study: {activeRun.study_id ?? "—"}</span>
                    <span>Comparator: {activeRun.comparator_id ?? "—"}</span>
                    <span>Candidate POD: {activeRun.candidate_pod_id ?? "—"}</span>
                  </div>
                </div>
              </div>

              <div className="subsection">
                <h3>Assumptions</h3>
                <ul className="bullet-list">
                  {activeRun.output.assumptions.map((assumption) => (
                    <li key={assumption}>{assumption}</li>
                  ))}
                </ul>
              </div>

              <div className="subsection">
                <h3>Warnings</h3>
                {activeRun.output.warnings.length ? (
                  <ul className="bullet-list">
                    {activeRun.output.warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="empty-copy">No warnings were returned for this run.</p>
                )}
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <p>
                Run one of the deterministic calculators to see the persisted
                response envelope from the backend.
              </p>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
