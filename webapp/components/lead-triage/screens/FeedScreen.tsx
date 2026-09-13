"use client";

import { FEED_STATS, RUN_FILTERS } from "../data/mockData";
import {
  useFilteredRuns,
  useLeadTriageNavigation,
} from "../context/LeadTriageNavigationContext";
import { ChevronRight } from "../ui/ChevronRight";
import { PipelineSteps } from "../ui/PipelineSteps";
import { SearchPill } from "../ui/SearchPill";
import { StatCard } from "../ui/StatCard";
import { StatusTag } from "../ui/StatusTag";
import { initialsFromName } from "../utils/format";
import { buildPipelineSegments } from "../utils/pipeline";

export function FeedScreen() {
  const { filter, setFilter, openRunDetail } = useLeadTriageNavigation();
  const runs = useFilteredRuns();

  return (
    <>
      <div className="ltc-stats">
        {FEED_STATS.map((stat) => (
          <StatCard
            key={stat.label}
            label={stat.label}
            value={stat.num}
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
        <div className="ltc-list">
          {runs.map((run) => (
            <div
              key={run.id}
              className="ltc-runcard"
              role="button"
              tabIndex={0}
              onClick={openRunDetail}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  openRunDetail();
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
                  {run.agent} · started {run.started}
                </div>
              </div>
              <StatusTag label={run.status} tagClass={run.tagClass} />
              <PipelineSteps segments={buildPipelineSegments(run.stage)} />
              <ChevronRight />
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
