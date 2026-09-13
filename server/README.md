# Lead Triage — multi-agent, multi-app

Five narrow agents behind a **deterministic** orchestrator. Least-privilege tool access enforced in code.
Apps: Gmail · HubSpot (or Airtable) · Slack · Google Calendar.

**Demo:** [Loom walkthrough](https://www.loom.com/share/3645cf220dc748ca809eda373ff8c8d5)

```
Gmail ─> Router ─> Extractor ─> Critic ─> CRM agent ─> Slack approval ─> Scheduler ─> Calendar + Gmail
          (no tools) (no tools) (no tools)  (crm only)      (human)      (cal+send only)
```

## Run order (today)

```bash
pip install -r requirements.txt
cp .env.example .env            # fill GEMINI_API_KEY first, everything else later

python tests_smoke.py           # 0 tokens: orchestration, registry, idempotency, retry, dry-run
python -m evals.run_evals       # fakes + real LLM: 25 cases, prints pass table
python demo.py inject           # rehearse the demo beats with fakes

# live
USE_FAKES=0 uvicorn server:app --port 8000 &
ngrok http 8000                 # paste https://…/slack/interact into Slack app > Interactivity
POLL=1 USE_FAKES=0 uvicorn server:app --port 8000
```

## Step-by-step build / wiring

1. **Gemini key** (`GEMINI_API_KEY`) in `.env`. Run `tests_smoke.py` (no key needed) then `evals` (key needed). Fix prompts until ≥ 20/25.
2. **Google** — Cloud console → **OAuth client (Desktop app, not service account)** → download JSON as `server/credentials.json` (must contain an `"installed"` key). Enable Gmail + Calendar APIs. Add your test account as a test user. First `USE_FAKES=0` run opens the consent screen once; `token.json` persists.
3. **HubSpot** — Settings → Integrations → **Private apps** → enable **all four** scopes: `crm.objects.contacts.read`, `crm.objects.contacts.write`, `crm.objects.deals.read`, `crm.objects.deals.write` → **regenerate token** → `HUBSPOT_TOKEN`. A 403 on `create_crm_deal` almost always means deals scopes are missing on the token. If it fights you for >30 min: `CRM_PROVIDER=airtable`, base with tables `Contacts(Email,Name,Company,Deals)` and `Deals(Title,Contact,Stage)`.
4. **Slack** — api.slack.com → new app → Bot scopes `chat:write` → install → `SLACK_BOT_TOKEN`, channel ID, signing secret. **Interactivity → Request URL** = `https://<your-ngrok-host>/slack/interact` (not `/slack/interactions` unless you use the built-in alias). Run `ngrok http 127.0.0.1:8000` while uvicorn is up; 502 from ngrok means nothing is listening on port 8000. Invite the bot to the channel.
5. **Live round trip** — `curl -X POST localhost:8000/ingest -H 'content-type: application/json' -d @evals/cases/happy_clean_lead.json` (send just the `email` object). Click Approve in Slack. Check calendar + inbox.
6. **Inspect any run** — `GET /runs/{id}` returns state history, every agent call (latency, tokens), every action (status: OK / REPLAYED / DRY_RUN / DENIED / FAILED).

## Reliability mechanisms (for the brief)

| Mechanism | Where | What it prevents |
|---|---|---|
| Table-driven state machine | `orchestrator/states.py` | LLM deciding control flow; illegal transitions |
| Least-privilege registry | `orchestrator/registry.py` + `executor.py` | Reader agents ever writing; injection reaching an app |
| Critic gate (conf < 0.7 → human, injection → quarantine) | `agents/critic.py` | Acting on bad extractions |
| Idempotency keys on every write | `executor.py` | Duplicate contacts/events on retry or replay |
| Retry w/ backoff on 429/5xx, then escalate | `executor.py` | Transient API failures becoming silent drops |
| Step cap (12) per agent | `agents/base.py` | Runaway loops |
| Human approval before any outbound action | `machine.py` | Unreviewed emails/bookings |
| Dry-run mode | `DRY_RUN=1` | Testing against live accounts |
| Email-ID dedupe + state check on approve | `machine.py` | Double processing, double-click booking |

## Demo beats (2 min)
happy → dup (show REPLAYED/updated) → inject (QUARANTINED, actions table empty of writes, show registry) → crm500 (3 retries then ESCALATED) → eval table.

## Cut list if behind at 1pm PT
Critic → set `CRITIC_THRESHOLD=0` (gate disabled, still logs). Router → hardcode `lead`. Calendar → keep Gmail/CRM/Slack = still 3 apps.
