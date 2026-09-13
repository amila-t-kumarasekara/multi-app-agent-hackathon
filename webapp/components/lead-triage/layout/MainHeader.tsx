"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { getScreenMeta } from "../data/mockData";
import { useLeadTriageNavigation } from "../context/LeadTriageNavigationContext";

export function MainHeader() {
  const { screen, setNewRunOpen, refreshFeed, setFeedMessage } = useLeadTriageNavigation();
  const { title, description, headerAction } = getScreenMeta(screen);
  const [pulling, setPulling] = useState(false);

  async function onHeaderAction() {
    if (screen !== "feed") return;
    setPulling(true);
    setFeedMessage(null);
    try {
      const res = await api.ingestFromGmail();
      refreshFeed();
      setFeedMessage(
        res.message ??
          (res.queued.length
            ? `Processing ${res.queued.length} unread email(s)…`
            : "No new unread emails in Gmail."),
      );
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Gmail sync failed";
      if (msg.includes("404")) {
        setFeedMessage(
          "API is missing POST /ingest/gmail — restart uvicorn or run: docker compose build server && docker compose up -d server. Use API URL http://127.0.0.1:8000 (not localhost) if Docker also uses port 8000.",
        );
      } else if (msg.includes("400")) {
        setFeedMessage("Gmail is not connected on this API process. Add token.json or run the server on the host.");
        setNewRunOpen(true);
      } else {
        setFeedMessage(msg);
        setNewRunOpen(true);
      }
    } finally {
      setPulling(false);
    }
  }

  return (
    <div className="ltc-topbar">
      <div>
        <h1 className="ltc-title">{title}</h1>
        <p className="ltc-desc">{description}</p>
      </div>
      {headerAction ? (
        <button
          type="button"
          className="btn btn-primary"
          onClick={onHeaderAction}
          disabled={screen !== "feed" || pulling}
        >
          {pulling ? "Checking Gmail…" : headerAction}
        </button>
      ) : null}
    </div>
  );
}
