"use client";

import { api, type ApiEscalation } from "@/lib/api";
import { useApiData } from "../hooks/useApiData";
import { StatusTag } from "../ui/StatusTag";
import { formatRelativeTime, initialsFromName } from "../utils/format";

export function EscalationScreen() {
  const { data: escalations, loading, error } = useApiData<ApiEscalation[]>(api.listEscalations, 5000);

  if (error) return <div className="ltc-listcard"><div className="ltc-empty">Couldn&apos;t load escalations: {error}</div></div>;
  if (loading && !escalations) return <div className="ltc-listcard"><div className="ltc-empty">Loading escalations…</div></div>;
  if (!escalations || escalations.length === 0) {
    return <div className="ltc-listcard"><div className="ltc-empty">Nothing escalated or quarantined right now.</div></div>;
  }

  return (
    <div className="ltc-listcard">
      <div className="ltc-rowlist">
        {escalations.map((item) => (
          <div key={item.id} className="ltc-rowcard">
            <div className="ltc-avatar ltc-avatar-accent">
              {initialsFromName(item.leadName)}
            </div>
            <div className="ltc-runinfo ltc-runinfo-grow">
              <div className="ltc-runname">
                {item.leadName}{" "}
                <span className="ltc-runcompany">— {item.company}</span>
              </div>
              <div className="ltc-runmeta">
                {item.reason} · flagged {formatRelativeTime(item.updatedAt)}
              </div>
            </div>
            <StatusTag label={item.risk} tagClass={item.riskClass} />
            <div className="ltc-actions">
              <button type="button" className="btn btn-ghost" disabled>
                Reject
              </button>
              <button type="button" className="btn btn-primary" disabled>
                Approve
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
