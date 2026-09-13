"use client";

import { useMemo } from "react";
import { api, type ApiAction, type ApiAgentCall, type ApiRunDetail } from "@/lib/api";
import type { IconName } from "../icons/iconPaths";
import { Icon } from "../icons/Icon";
import { useLeadTriageNavigation } from "../context/LeadTriageNavigationContext";
import { useApiData } from "../hooks/useApiData";

const TOOL_ICON: Record<string, IconName> = {
  search_crm_contact: "database",
  create_crm_contact: "database",
  update_crm_contact: "database",
  create_crm_deal: "database",
  get_calendar_availability: "calendar",
  create_calendar_event: "calendar",
  send_email_reply: "mail",
  post_slack_approval: "message",
  post_slack_message: "message",
};

type TraceStep = {
  key: string;
  title: string;
  time: number;
  duration: string;
  icon: IconName;
  done: boolean;
  payload: string | null;
};

function shortJson(raw: string, max = 160): string {
  try {
    const parsed = JSON.parse(raw);
    const s = JSON.stringify(parsed);
    return s.length > max ? `${s.slice(0, max)}…` : s;
  } catch {
    return raw.length > max ? `${raw.slice(0, max)}…` : raw;
  }
}

function buildTrace(detail: ApiRunDetail): TraceStep[] {
  const { run, agent_calls, actions } = detail;
  const ctx = run.context as { email?: { from?: string; subject?: string } };
  const email = ctx.email ?? {};

  const steps: TraceStep[] = [
    {
      key: "received",
      title: "Email received",
      time: run.created_at,
      duration: "—",
      icon: "mail",
      done: true,
      payload: `from: ${email.from ?? "unknown"}${email.subject ? ` · subject: "${email.subject}"` : ""}`,
    },
  ];

  agent_calls.forEach((call: ApiAgentCall) => {
    steps.push({
      key: `call-${call.id}`,
      title: `${call.agent} agent → ${call.state_out || "done"}`,
      time: call.created_at,
      duration: `${(call.latency_ms / 1000).toFixed(1)}s`,
      icon: "bot",
      done: true,
      payload: shortJson(call.output),
    });
  });

  actions.forEach((action: ApiAction) => {
    steps.push({
      key: `action-${action.id}`,
      title: `${action.tool} — ${action.status}`,
      time: action.created_at,
      duration: "—",
      icon: TOOL_ICON[action.tool] ?? "activity",
      done: action.status !== "DENIED" && action.status !== "FAILED" && action.status !== "FAILED_RETRIES",
      payload: shortJson(action.result),
    });
  });

  return steps.sort((a, b) => a.time - b.time);
}

export function RunDetailScreen() {
  const { selectedRunId } = useLeadTriageNavigation();
  const fetcher = useMemo(
    () => (selectedRunId ? () => api.getRun(selectedRunId) : null),
    [selectedRunId],
  );
  const { data, loading, error } = useApiData<ApiRunDetail>(fetcher, 5000);

  if (!selectedRunId) {
    return (
      <div className="ltc-detailcard">
        <div className="card-body">Select a run from the live feed to see its trace.</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ltc-detailcard">
        <div className="card-body">Couldn&apos;t load run {selectedRunId}: {error}</div>
      </div>
    );
  }

  if (loading && !data) {
    return (
      <div className="ltc-detailcard">
        <div className="card-body">Loading run {selectedRunId}…</div>
      </div>
    );
  }

  if (!data) return null;

  const { run } = data;
  const ctx = run.context as {
    email?: { from?: string; subject?: string };
    extraction?: { name?: string | null; company?: string | null };
  };
  const email = ctx.email ?? {};
  const extraction = ctx.extraction ?? {};
  const leadName = extraction.name || email.from?.split("<")[0].trim() || "Unknown";
  const company = extraction.company || "—";
  const durationS = (run.updated_at - run.created_at).toFixed(1);
  const steps = buildTrace(data);

  return (
    <>
      <div className="ltc-detailcard">
        <div className="card-kicker">
          Run #{run.id} · {leadName}
        </div>
        <div className="card-title">{company}</div>
        <p className="card-body">
          State: {run.state} · Duration so far: {durationS}s
        </p>
      </div>

      <div className="ltc-detailcard">
        <div className="ltc-trace">
          {steps.map((step, index) => {
            const hasLine = index < steps.length - 1;
            const dotStyle = step.done
              ? { background: "var(--color-accent-2-500)", color: "white" }
              : { background: "var(--color-accent)", color: "white" };

            return (
              <div key={step.key} className="ltc-tracestep">
                {hasLine ? <div className="ltc-traceline" aria-hidden /> : null}
                <div className="ltc-tracedot" style={dotStyle}>
                  <Icon name={step.icon} size={15} />
                </div>
                <div className="ltc-tracebody">
                  <div className="ltc-tracetitle">{step.title}</div>
                  <div className="ltc-tracemeta">
                    {new Date(step.time * 1000).toLocaleTimeString()} · {step.duration}
                  </div>
                  {step.payload ? (
                    <div className="ltc-payload">{step.payload}</div>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}
