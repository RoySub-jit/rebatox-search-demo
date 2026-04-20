export type CalculationType =
  | "mg_per_kg_day_to_mg_per_day"
  | "mg_per_day_to_mg_per_kg_day"
  | "margin_of_exposure"
  | "pde"
  | "ade";

export type CalculationOutput = {
  calculator: string;
  formula: string;
  inputs: Record<string, string | number>;
  assumptions: string[];
  result: Record<string, string | number | boolean | null> | null;
  warnings: string[];
  status: "ok" | "warning" | "error";
};

export type CalculationRunResponse = {
  id: number;
  run_type: CalculationType;
  status: "ok" | "warning";
  product_id: number | null;
  comparator_id: number | null;
  study_id: number | null;
  candidate_pod_id: number | null;
  inputs: Record<string, string | number>;
  output: CalculationOutput;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type RunCalculationPayload = {
  run_type: CalculationType;
  inputs: Record<string, string>;
  product_id?: number;
  comparator_id?: number;
  study_id?: number;
  candidate_pod_id?: number;
};

type ApiErrorPayload = {
  detail?:
    | {
        code?: string;
        message?: string;
      }
    | string;
};

export class ApiClientError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
  }
}

async function requestJson<T>(
  apiBaseUrl: string,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let message = "Request failed.";
    let code: string | undefined;

    try {
      const payload = (await response.json()) as ApiErrorPayload;
      if (typeof payload.detail === "string") {
        message = payload.detail;
      } else if (payload.detail) {
        message = payload.detail.message ?? message;
        code = payload.detail.code;
      }
    } catch {
      message = response.statusText || message;
    }

    throw new ApiClientError(message, response.status, code);
  }

  return (await response.json()) as T;
}

export function runCalculation(
  apiBaseUrl: string,
  payload: RunCalculationPayload,
) {
  return requestJson<CalculationRunResponse>(
    apiBaseUrl,
    "/api/v1/calculations/run",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function getCalculationRun(apiBaseUrl: string, calculationId: number) {
  return requestJson<CalculationRunResponse>(
    apiBaseUrl,
    `/api/v1/calculations/${calculationId}`,
    {
      method: "GET",
    },
  );
}
