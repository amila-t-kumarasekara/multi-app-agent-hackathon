import { INTEGRATIONS } from "../data/mockData";
import { Icon } from "../icons/Icon";
import { StatusTag } from "../ui/StatusTag";

export function IntegrationsScreen() {
  return (
    <div className="ltc-listcard">
      <div className="ltc-rowlist">
        {INTEGRATIONS.map((integration) => {
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
                <Icon name={integration.icon} size={18} />
              </div>
              <div className="ltc-runinfo ltc-runinfo-grow">
                <div className="ltc-runname">{integration.name}</div>
                <div className="ltc-runmeta">{integration.account}</div>
              </div>
              <StatusTag
                label={integration.status}
                tagClass={integration.statusClass}
              />
              <div className="ltc-actions">
                <button type="button" className="btn btn-secondary">
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
