const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`${path} -> ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export type ApiTagClass = "tag-accent" | "tag-accent-2" | "tag-neutral" | "tag-outline";

export type ApiRun = {
  id: string;
  emailId: string;
  leadName: string;
  company: string;
  agent: string;
  state: string;
  status: "Running" | "Completed" | "Escalated" | "Failed";
  tagClass: ApiTagClass;
  stage: number;
  createdAt: number;
  updatedAt: number;
  note: string | null;
};

export type ApiEscalation = ApiRun & {
  reason: string;
  risk: "High" | "Medium" | "Low";
  riskClass: ApiTagClass;
};

export type ApiAgentCall = {
  id: number;
  run_id: string;
  agent: string;
  state_in: string;
  state_out: string;
  input: string;
  output: string;
  latency_ms: number;
  tokens_in: number;
  tokens_out: number;
  created_at: number;
};

export type ApiAction = {
  id: number;
  run_id: string;
  agent: string;
  tool: string;
  args: string;
  result: string;
  status: string;
  idem_key: string | null;
  created_at: number;
};

export type ApiRunDetail = {
  run: { id: string; email_id: string; state: string; context: Record<string, unknown>; created_at: number; updated_at: number };
  agent_calls: ApiAgentCall[];
  actions: ApiAction[];
};

export type ApiAgent = {
  name: string;
  role: string;
  model: string;
  status: string;
  statusClass: ApiTagClass;
  runsToday: number;
  tools: string[];
};

export type ApiIntegration = {
  name: string;
  icon: string;
  account: string;
  detail?: string;
  status: "Connected" | "Disconnected";
  statusClass: ApiTagClass;
  actionLabel: string;
};

export type ApiEvalMetric = { label: string; value: string; trend: string; up: boolean };
export type ApiEvalCase = { name: string; category: string; result: "Pass" | "Fail"; latency: string };
export type ApiEvalSummary = { metrics: ApiEvalMetric[]; cases: ApiEvalCase[] };

export type ApiStats = {
  runsToday: number;
  autoResolvedPct: number | null;
  inEscalation: number;
  avgFirstActionS: number;
};

export const api = {
  listRuns: () => apiFetch<ApiRun[]>("/runs"),
  getRun: (id: string) => apiFetch<ApiRunDetail>(`/runs/${id}`),
  listEscalations: () => apiFetch<ApiEscalation[]>("/escalations"),
  listAgents: () => apiFetch<ApiAgent[]>("/agents"),
  listIntegrations: () => apiFetch<ApiIntegration[]>("/integrations"),
  getEvalSummary: () => apiFetch<ApiEvalSummary | null>("/evals"),
  getStats: () => apiFetch<ApiStats>("/stats"),
};
