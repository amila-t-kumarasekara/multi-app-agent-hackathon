"use client";

import { useCallback, useState } from "react";
import { api, type ApiEscalation } from "@/lib/api";
import { useApiData } from "../hooks/useApiData";
import { StatusTag } from "../ui/StatusTag";
import { formatRelativeTime, initialsFromName } from "../utils/format";

export function EscalationScreen() {
  const [reloadToken, setReloadToken] = useState(0);
  const [pending, setPending] = useState<Record<string, "approve" | "reject">>({});
  const [actionError, setActionError] = useState<string | null>(null);

  const { data: escalations, loading, error } = useApiData<ApiEscalation[]>(
    api.listEscalations,
    5000,
    reloadToken,
  );

  const decide = useCallback(async (runId: string, decision: "approve" | "reject") => {
    setActionError(null);
    setPending((p) => ({ ...p, [runId]: decision }));
    try {
      const result = await api.decideRun(runId, decision);
      if (result.error) {
        setActionError(result.error);
      } else if (result.skipped) {
        setActionError(result.skipped);
      }
      setReloadToken((t) => t + 1);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setPending((p) => {
        const next = { ...p };
        delete next[runId];
        return next;
      });
    }
  }, []);

  if (error) {
    return (
      <div className="ltc-listcard">
        <div className="ltc-empty">Couldn&apos;t load escalations: {error}</div>
      </div>
    );
  }
  if (loading && !escalations) {
    return (
      <div className="ltc-listcard">
        <div className="ltc-empty">Loading escalations…</div>
      </div>
    );
  }
  if (!escalations || escalations.length === 0) {
    return (
      <div className="ltc-listcard">
        <div className="ltc-empty">Nothing escalated or quarantined right now.</div>
      </div>
    );
  }

  return (
    <div className="ltc-listcard">
      {actionError ? (
        <div className="ltc-empty" style={{ marginBottom: "0.75rem" }}>
          {actionError}
        </div>
      ) : null}
      <div className="ltc-rowlist">
        {escalations.map((item) => {
          const busy = pending[item.id];
          return (
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
                <button
                  type="button"
                  className="btn btn-ghost"
                  disabled={!!busy}
                  onClick={() => decide(item.id, "reject")}
                >
                  {busy === "reject" ? "Rejecting…" : "Reject"}
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={!!busy}
                  onClick={() => decide(item.id, "approve")}
                >
                  {busy === "approve" ? "Approving…" : "Approve"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
