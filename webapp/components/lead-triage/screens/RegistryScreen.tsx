import { AGENTS } from "../data/mockData";
import { Icon } from "../icons/Icon";
import { StatusTag } from "../ui/StatusTag";

export function RegistryScreen() {
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
          {AGENTS.map((agent) => (
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
                  {agent.tools.map((tool) => (
                    <div
                      key={tool}
                      className="ltc-toolchip"
                      style={{
                        background: "var(--color-accent-2-100)",
                        color: "var(--color-accent-2-800)",
                      }}
                      title={tool}
                    >
                      <Icon name={tool} size={13} />
                    </div>
                  ))}
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
