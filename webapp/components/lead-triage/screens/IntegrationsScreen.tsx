"use client";

import { api, type ApiIntegration } from "@/lib/api";
import type { IconName } from "../icons/iconPaths";
import { Icon } from "../icons/Icon";
import { useApiData } from "../hooks/useApiData";
import { StatusTag } from "../ui/StatusTag";

export function IntegrationsScreen() {
  const { data: integrations, loading, error } = useApiData<ApiIntegration[]>(api.listIntegrations, 10000);

  if (error) return <div className="ltc-listcard"><div className="ltc-empty">Couldn&apos;t load integrations: {error}</div></div>;
  if (loading && !integrations) return <div className="ltc-listcard"><div className="ltc-empty">Loading integrations…</div></div>;

  return (
    <div className="ltc-listcard">
      <div className="ltc-rowlist">
        {(integrations ?? []).map((integration) => {
          const iconStyle =
            integration.status === "Connected"
              ? {
                  background: "var(--color-accent-2-100)",
                  color: "var(--color-accent-2-800)",
                }
              : {
                  background: "var(--color-neutral-200)",
                  color: "var(--color-neutral-600)",
                };

          return (
            <div key={integration.name} className="ltc-rowcard">
              <div className="ltc-inticon" style={iconStyle}>
                <Icon name={integration.icon as IconName} size={18} />
              </div>
              <div className="ltc-runinfo ltc-runinfo-grow">
                <div className="ltc-runname">{integration.name}</div>
                <div className="ltc-runmeta">{integration.account}</div>
                {integration.detail ? (
                  <div className="ltc-runmeta" style={{ marginTop: 4, opacity: 0.85 }}>
                    {integration.detail}
                  </div>
                ) : null}
              </div>
              <StatusTag
                label={integration.status}
                tagClass={integration.statusClass}
              />
              <div className="ltc-actions">
                <button type="button" className="btn btn-secondary" disabled>
                  {integration.actionLabel}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
