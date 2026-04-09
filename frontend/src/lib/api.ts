export type ApiError = {
  message: string;
  status?: number;
  detail?: unknown;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/+$/, "") || "http://localhost:8000/api";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path.startsWith("/") ? "" : "/"}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers || {}),
    },
  });

  const contentType = res.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await res.json().catch(() => null)
    : await res.text().catch(() => "");

  if (!res.ok) {
    const err: ApiError = {
      message: "Request failed",
      status: res.status,
      detail: body,
    };
    throw err;
  }
  return body as T;
}

export type SimulateRequest = {
  topic: string;
  rounds?: number;
  custom_roles?: string[];
  temperature?: number;
};

export type SimulationMessage = {
  simulation_id: string;
  round: number;
  agent_role: string;
  agent_personality?: string;
  content: string;
  timestamp?: string;
  meta?: Record<string, unknown>;
};

export type SimulateResponse = {
  simulation_id: string;
  status: string;
  topic: string;
  rounds_completed: number;
  messages: SimulationMessage[];
  consensus?: Record<string, unknown> | null;
  final_prediction?: Record<string, unknown>;
};

export async function simulate(req: SimulateRequest) {
  return requestJson<SimulateResponse>("/simulate/", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export type PredictRequest = {
  topic: string;
  rounds?: number;
  include_sentiment?: boolean;
};

export type PredictResponse = {
  simulation_id: string;
  topic: string;
  prediction: Record<string, unknown>;
  messages_count: number;
  sentiment?: Record<string, unknown> | null;
};

export async function predict(req: PredictRequest) {
  return requestJson<PredictResponse>("/predict/", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export type ButterflyRequest = {
  topic: string;
  simulation_id: string;
  alternative_scenario: string;
};

export type ButterflyResponse = {
  original_simulation_id: string;
  topic: string;
  alternative_scenario: string;
  analysis: Record<string, unknown>;
};

export async function butterflyEffect(req: ButterflyRequest) {
  return requestJson<ButterflyResponse>("/predict/butterfly-effect", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export type SimulationStatusResponse = {
  status: string;
  agents?: Array<{ role: string; personality?: string; id?: string }>;
  topic?: string;
  messages?: SimulationMessage[];
  consensus?: Record<string, unknown> | null;
  final_prediction?: Record<string, unknown>;
};

export async function getSimulationStatus(simulation_id: string) {
  return requestJson<SimulationStatusResponse>(`/simulate/status/${encodeURIComponent(simulation_id)}`, {
    method: "GET",
  });
}

