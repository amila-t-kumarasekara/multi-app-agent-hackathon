"use client";

import { api, type ApiAgent } from "@/lib/api";
import type { IconName } from "../icons/iconPaths";
import { Icon } from "../icons/Icon";
import { useApiData } from "../hooks/useApiData";
import { StatusTag } from "../ui/StatusTag";

export function RegistryScreen() {
  const { data: agents, loading, error } = useApiData<ApiAgent[]>(api.listAgents, 5000);

  if (error) return <div className="ltc-listcard"><div className="ltc-empty">Couldn&apos;t load agent registry: {error}</div></div>;
  if (loading && !agents) return <div className="ltc-listcard"><div className="ltc-empty">Loading agent registry…</div></div>;

  return (
    <div className="ltc-listcard ltc-tablewrap">
      <table className="table">
        <thead>
          <tr>
            <th>Agent</th>
            <th>Model</th>
            <th>Tool access</th>
            <th>Status</th>
            <th>Runs today</th>
          </tr>
        </thead>
        <tbody>
          {(agents ?? []).map((agent) => (
            <tr key={agent.name}>
              <td>
                <strong>{agent.name}</strong>
                <div style={{ fontSize: 12.5, opacity: 0.55, marginTop: 2 }}>
                  {agent.role}
                </div>
              </td>
              <td className="text-muted">{agent.model}</td>
              <td>
                <div className="ltc-toolgrid">
                  {agent.tools.length === 0 ? (
                    <span className="text-muted" style={{ fontSize: 12.5 }}>none</span>
                  ) : (
                    agent.tools.map((tool) => (
                      <div
                        key={tool}
                        className="ltc-toolchip"
                        style={{
                          background: "var(--color-accent-2-100)",
                          color: "var(--color-accent-2-800)",
                        }}
                        title={tool}
                      >
                        <Icon name={tool as IconName} size={13} />
                      </div>
                    ))
                  )}
                </div>
              </td>
              <td>
                <StatusTag label={agent.status} tagClass={agent.statusClass} />
              </td>
              <td className="text-muted">{agent.runsToday}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
