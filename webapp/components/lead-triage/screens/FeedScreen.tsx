"use client";

import { useMemo } from "react";
import { api, type ApiRun, type ApiStats } from "@/lib/api";
import { RUN_FILTERS } from "../data/mockData";
import {
  useLeadTriageNavigation,
} from "../context/LeadTriageNavigationContext";
import { useApiData } from "../hooks/useApiData";
import { ChevronRight } from "../ui/ChevronRight";
import { PipelineSteps } from "../ui/PipelineSteps";
import { SearchPill } from "../ui/SearchPill";
import { StatCard } from "../ui/StatCard";
import { StatusTag } from "../ui/StatusTag";
import { formatRelativeTime, initialsFromName } from "../utils/format";
import { buildPipelineSegments } from "../utils/pipeline";

function buildStatCards(stats: ApiStats | null) {
  return [
    {
      label: "Runs today",
      value: stats ? String(stats.runsToday) : "—",
      trend: "since midnight",
      up: true,
      icon: "activity" as const,
      iconBg: "var(--color-accent-2-100)",
      iconFg: "var(--color-accent-2-800)",
    },
    {
      label: "Auto-resolved",
      value: stats?.autoResolvedPct != null ? `${stats.autoResolvedPct.toFixed(1)}%` : "—",
      trend: "of terminal runs",
      up: true,
      icon: "check" as const,
      iconBg: "var(--color-accent-2-100)",
      iconFg: "var(--color-accent-2-800)",
    },
    {
      label: "In escalation",
      value: stats ? String(stats.inEscalation) : "—",
      trend: "needs review",
      up: false,
      icon: "flag" as const,
      iconBg: "var(--color-accent-100)",
      iconFg: "var(--color-accent-800)",
    },
    {
      label: "Avg. time to first action",
      value: stats ? `${stats.avgFirstActionS.toFixed(1)}s` : "—",
      trend: "router latency",
      up: false,
      icon: "clock" as const,
      iconBg: "var(--color-accent-100)",
      iconFg: "var(--color-accent-800)",
    },
  ];
}

export function FeedScreen() {
  const { filter, setFilter, openRunDetail } = useLeadTriageNavigation();
  const { data: runs, loading, error } = useApiData<ApiRun[]>(api.listRuns, 5000);
  const { data: stats } = useApiData<ApiStats>(api.getStats, 5000);

  const filteredRuns = useMemo(
    () => (runs ?? []).filter((run) => filter === "All runs" || run.status === filter),
    [runs, filter],
  );

  const statCards = buildStatCards(stats ?? null);

  return (
    <>
      <div className="ltc-stats">
        {statCards.map((stat) => (
          <StatCard
            key={stat.label}
            label={stat.label}
            value={stat.value}
            trend={stat.trend}
            up={stat.up}
            icon={stat.icon}
            iconBg={stat.iconBg}
            iconFg={stat.iconFg}
          />
        ))}
      </div>

      <div className="ltc-filters">
        {RUN_FILTERS.map((label) => (
          <button
            key={label}
            type="button"
            className={
              filter === label ? "ltc-fbtn ltc-fbtn-active" : "ltc-fbtn"
            }
            onClick={() => setFilter(label)}
          >
            {label}
          </button>
        ))}
        <SearchPill />
      </div>

      <div className="ltc-listcard">
        {error ? (
          <div className="ltc-empty">Couldn&apos;t reach the server at {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"} — is it running?</div>
        ) : loading && !runs ? (
          <div className="ltc-empty">Loading runs…</div>
        ) : filteredRuns.length === 0 ? (
          <div className="ltc-empty">No runs yet. POST an email to /ingest to see one here.</div>
        ) : (
          <div className="ltc-list">
            {filteredRuns.map((run) => (
              <div
                key={run.id}
                className="ltc-runcard"
                role="button"
                tabIndex={0}
                onClick={() => openRunDetail(run.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    openRunDetail(run.id);
                  }
                }}
              >
                <div className="ltc-avatar">{initialsFromName(run.leadName)}</div>
                <div className="ltc-runinfo">
                  <div className="ltc-runname">
                    {run.leadName}{" "}
                    <span className="ltc-runcompany">— {run.company}</span>
                  </div>
                  <div className="ltc-runmeta">
                    {run.agent} · started {formatRelativeTime(run.createdAt)}
                  </div>
                </div>
                <StatusTag label={run.status} tagClass={run.tagClass} />
                <PipelineSteps segments={buildPipelineSegments(run.stage)} />
                <ChevronRight />
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
