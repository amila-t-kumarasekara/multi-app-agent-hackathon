"use client";

import { NAV_ITEMS } from "../data/mockData";
import { useLeadTriageNavigation } from "../context/LeadTriageNavigationContext";
import { Icon } from "../icons/Icon";

export function Sidebar() {
  const { screen, setScreen } = useLeadTriageNavigation();

  return (
    <aside className="ltc-side">
      <div className="ltc-brand">
        <div className="ltc-brand-mark">
          <Icon name="bot" size={20} />
        </div>
        <div>
          <div className="ltc-brand-name">Furrow</div>
          <div className="ltc-brand-sub">Lead triage ops</div>
        </div>
      </div>

      <div>
        <div className="ltc-navlabel">Workspace</div>
        <nav className="ltc-nav" aria-label="Workspace">
          {NAV_ITEMS.map((item) => {
            const active = screen === item.key;
            return (
              <button
                key={item.key}
                type="button"
                className={
                  active ? "ltc-navlink ltc-navlink-active" : "ltc-navlink"
                }
                onClick={() => setScreen(item.key)}
                aria-current={active ? "page" : undefined}
              >
                <span className="ltc-navicon">
                  <Icon name={item.icon} size={15} />
                </span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="ltc-side-foot">
        <span className="ltc-side-foot-dot" aria-hidden />
        <span className="ltc-side-foot-text">All systems operational</span>
      </div>
    </aside>
  );
}
