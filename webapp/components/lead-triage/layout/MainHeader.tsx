"use client";

import { getScreenMeta } from "../data/mockData";
import { useLeadTriageNavigation } from "../context/LeadTriageNavigationContext";

export function MainHeader() {
  const { screen } = useLeadTriageNavigation();
  const { title, description, headerAction } = getScreenMeta(screen);

  return (
    <div className="ltc-topbar">
      <div>
        <h1 className="ltc-title">{title}</h1>
        <p className="ltc-desc">{description}</p>
      </div>
      {headerAction ? (
        <button type="button" className="btn btn-primary">
          {headerAction}
        </button>
      ) : null}
    </div>
  );
}
