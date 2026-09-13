"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useLeadTriageNavigation } from "../context/LeadTriageNavigationContext";

/** Fallback when Gmail is not connected — optional test email without OAuth. */
export function NewRunModal() {
  const { newRunOpen, setNewRunOpen, refreshFeed, setFeedMessage } = useLeadTriageNavigation();
  const [from, setFrom] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!newRunOpen) return null;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    const id = `web-${Date.now()}`;
    try {
      await api.ingestEmail({
        id,
        thread_id: `t-${id}`,
        from,
        subject,
        body,
      });
      setNewRunOpen(false);
      setFrom("");
      setSubject("");
      setBody("");
      setFeedMessage("Test email queued — agents are processing it.");
      refreshFeed();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start run");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="ltc-modal-backdrop" role="presentation" onClick={() => setNewRunOpen(false)}>
      <div
        className="ltc-modal"
        role="dialog"
        aria-labelledby="new-run-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="new-run-title" className="ltc-modal-title">Simulate test email</h2>
        <p className="ltc-modal-desc">
          Gmail isn&apos;t connected, so you can paste a fake inbound message here. When Gmail is
          connected, <strong>New run</strong> pulls real unread mail automatically — no form needed.
        </p>
        <form onSubmit={onSubmit} className="ltc-modal-form">
          <label className="ltc-field">
            <span>From</span>
            <input
              required
              type="text"
              placeholder="Jane Doe &lt;jane@acme.com&gt;"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
            />
          </label>
          <label className="ltc-field">
            <span>Subject</span>
            <input
              required
              type="text"
              placeholder="Demo request"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
          </label>
          <label className="ltc-field">
            <span>Body</span>
            <textarea
              required
              rows={5}
              placeholder="Hi, we'd like to schedule a demo…"
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
          </label>
          {error ? <p className="ltc-modal-error">{error}</p> : null}
          <div className="ltc-modal-actions">
            <button type="button" className="btn btn-secondary" onClick={() => setNewRunOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Starting…" : "Queue test email"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
