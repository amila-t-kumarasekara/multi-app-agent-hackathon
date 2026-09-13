import { ESCALATIONS } from "../data/mockData";
import { StatusTag } from "../ui/StatusTag";
import { initialsFromName } from "../utils/format";

export function EscalationScreen() {
  return (
    <div className="ltc-listcard">
      <div className="ltc-rowlist">
        {ESCALATIONS.map((item) => (
          <div key={`${item.leadName}-${item.company}`} className="ltc-rowcard">
            <div className="ltc-avatar ltc-avatar-accent">
              {initialsFromName(item.leadName)}
            </div>
            <div className="ltc-runinfo ltc-runinfo-grow">
              <div className="ltc-runname">
                {item.leadName}{" "}
                <span className="ltc-runcompany">— {item.company}</span>
              </div>
              <div className="ltc-runmeta">
                {item.reason} · flagged {item.age}
              </div>
            </div>
            <StatusTag label={item.risk} tagClass={item.riskClass} />
            <div className="ltc-actions">
              <button type="button" className="btn btn-ghost">
                Reject
              </button>
              <button type="button" className="btn btn-primary">
                Approve
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
