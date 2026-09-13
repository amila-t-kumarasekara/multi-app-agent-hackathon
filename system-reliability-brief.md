# System & Reliability Brief — Lead Triage

## Design thesis

Most "AI agent" demos give one model every tool and hope the system prompt keeps it honest. This project takes the opposite approach: **each agent gets the minimum tool access it needs to do its one job, enforced in code — not in a prompt.**

The email-reading agent cannot write to anything. The agent that writes to the CRM cannot send email or book meetings. The agent that books meetings and sends email can only run *after* a human clicks Approve. This makes prompt injection **structurally survivable** rather than something patched after the fact — and it means the highest-consequence agent in the system is the one with the least autonomy.

The control flow itself is a **deterministic state machine, not an LLM**. The LLM decides classifications and content; the orchestrator decides what happens next, by table lookup. That single choice is why every run is inspectable, replayable, and testable.

## Architecture

```
                    ┌─────────────┐
   Gmail ──────────>│   Router    │ lead / not-lead / ambiguous
                    └──────┬──────┘
                           v
                    ┌─────────────┐
                    │ Extractor   │  read-only, sandboxed
                    └──────┬──────┘
                           v
                    ┌─────────────┐
                    │  Critic     │  no tools at all
                    └──────┬──────┘
                           v
                    ┌─────────────┐
   Orchestrator ───>│    CRM      │  crm writes only
   (state machine)  └──────┬──────┘
                           v
                    ┌─────────────┐
                    │  Scheduler  │  calendar + send only
                    └─────────────┘
                           │
                  Slack approval gate
```

The orchestrator is a deterministic state machine (`server/orchestrator/states.py` + `server/orchestrator/machine.py`) that routes between agents by table lookup on each agent's structured output. An LLM orchestrator is nondeterministic, untestable, and unpredictable under load — this design trades a bit of flexibility for something that can actually be reasoned about, tested, and demoed reliably.

Least-privilege tool access is enforced by a static registry (`server/orchestrator/registry.py`), checked on every tool call inside `server/tools/executor.py`. An agent calling a tool outside its registry entry raises `ToolAccessDenied` — a hard stop, not a suggestion.

## The five agents

| Agent | Model | Tools | Job |
|---|---|---|---|
| **Router** | fast | none | Classifies inbound mail as `lead`, `not_lead`, or `ambiguous`. Kills newsletters and vendor spam before anything expensive runs. `ambiguous` goes straight to human review. |
| **Extractor** | smart | none | Pulls `name`, `email`, `company`, `intent`, `urgency`, `timing_preference` into a strict JSON schema from the raw email body. Untrusted content enters here and never becomes instructions — it's just data. |
| **Critic** | fast | none | Scores the extraction: `confidence` (0–1), `missing_fields`, and an `injection` flag. Below `CRITIC_THRESHOLD` (default `0.7`) the run escalates to a human instead of proceeding. Injection detected → quarantined immediately. |
| **CRM agent** | smart | `search_crm_contact`, `create_crm_contact`, `update_crm_contact`, `create_crm_deal` | Dedupes and syncs the qualified lead into HubSpot/Airtable. Cannot email, cannot book a meeting. |
| **Scheduler** | smart | `get_calendar_availability`, `create_calendar_event`, `send_email_reply` | Only ever invoked after a human clicks Approve in Slack. Books the intro call and sends the confirmation. |

## Reliability mechanisms

| Mechanism | Where | What it prevents |
|---|---|---|
| Idempotency keys on every write | `tools/executor.py` | Duplicate contacts/events on retry or replay |
| Retry with backoff on 429/5xx | `tools/executor.py` | Transient API failures becoming silent drops |
| Step cap per agent | `agents/base.py` | Runaway tool-calling loops |
| Dry-run mode | `DRY_RUN=1` | Testing against live accounts with zero writes |
| Email-ID dedupe + state check | `orchestrator/machine.py` | Reprocessing the same email; double-booking on double-click |

## Testing & verification

- `python tests_smoke.py` — 0-token orchestration tests covering routing, registry enforcement, idempotency, retry, and dry-run behavior against stubbed agents.
- `python -m evals.run_evals` — 25-case eval suite against fakes plus real Gemini calls, producing a pass table.
- `USE_FAKES=1` (default) runs the entire pipeline — Router → Extractor → Critic → CRM → Slack approval → Scheduler — against in-memory fakes for every app, so correctness can be verified with zero external accounts and zero live-side-effect risk.
