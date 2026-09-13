# Lead Triage — multi-agent, multi-app

An inbound-email lead triage system built on **five narrow AI agents behind one deterministic orchestrator**. It reads Gmail, classifies and qualifies leads, syncs them into a CRM (HubSpot or Airtable), routes every decision through a human approval gate in Slack, and books the intro call on Google Calendar — with a Next.js dashboard to watch it all happen live.

Apps wired in: **Gmail** · **HubSpot** (or Airtable) · **Slack** · **Google Calendar** · **Gemini** (LLM).

---

## Table of contents

- [What this project is](#what-this-project-is)
- [Architecture](#architecture)
- [The five agents](#the-five-agents)
- [Project layout](#project-layout)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
  - [Gemini API key](#gemini-api-key)
  - [HubSpot private app token](#hubspot-private-app-token)
  - [Slack app tokens](#slack-app-tokens)
  - [Google OAuth credentials (Gmail + Calendar)](#google-oauth-credentials-gmail--calendar)
- [Running it](#running-it)
  - [Option A: Docker Compose](#option-a-docker-compose)
  - [Option B: run locally with make](#option-b-run-locally-with-make)
  - [Option C: run manually](#option-c-run-manually)
- [Testing without live integrations](#testing-without-live-integrations)
- [Exposing Slack interactivity with ngrok](#exposing-slack-interactivity-with-ngrok)
- [Useful endpoints](#useful-endpoints)
- [Troubleshooting](#troubleshooting)

---

## What this project is

Most "AI agent" demos give one model every tool and hope the system prompt keeps it honest. This project takes the opposite approach: **each agent gets the minimum tool access it needs to do its one job, enforced in code — not in a prompt.**

The email-reading agent cannot write to anything. The agent that writes to the CRM cannot send email or book meetings. The agent that books meetings and sends email can only run *after* a human clicks Approve. This is what makes prompt injection **structurally survivable** rather than something you have to prompt-patch after the fact.

The control flow itself is a **deterministic state machine**, not an LLM. The LLM decides classifications and content; the *orchestrator* decides what happens next, by table lookup. That single choice is why every run is inspectable, replayable, and testable.

---

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

The orchestrator is **not** an LLM. It's a deterministic state machine (`server/orchestrator/states.py` + `server/orchestrator/machine.py`) that routes between agents by table lookup on each agent's structured output. An LLM orchestrator is nondeterministic, untestable, and unpredictable under load — this design trades a bit of flexibility for something you can actually reason about, test, and demo reliably.

Least-privilege tool access is enforced by a static registry (`server/orchestrator/registry.py`) checked on every tool call inside `server/tools/executor.py`. An agent calling a tool outside its registry entry raises `ToolAccessDenied` — it's not a suggestion, it's a hard stop.

### The five agents

| Agent | Model | Tools | Job |
|---|---|---|---|
| **Router** | fast | none | Classifies inbound mail as `lead`, `not_lead`, or `ambiguous`. Kills newsletters and vendor spam before anything expensive runs. `ambiguous` goes straight to human review. |
| **Extractor** | smart | none | Pulls `name`, `email`, `company`, `intent`, `urgency`, `timing_preference` into a strict JSON schema from the raw email body. Untrusted content enters here and never becomes instructions — it's just data. |
| **Critic** | fast | none | Scores the extraction: `confidence` (0–1), `missing_fields`, and an `injection` flag. Below `CRITIC_THRESHOLD` (default `0.7`) the run escalates to a human instead of proceeding. Injection detected → quarantined immediately. |
| **CRM agent** | smart | `search_crm_contact`, `create_crm_contact`, `update_crm_contact`, `create_crm_deal` | Dedupes and syncs the qualified lead into HubSpot/Airtable. Cannot email, cannot book a meeting. |
| **Scheduler** | smart | `get_calendar_availability`, `create_calendar_event`, `send_email_reply` | Only ever invoked **after a human clicks Approve in Slack**. Books the intro call and sends the confirmation. The highest-consequence agent is the one with the least autonomy. |

Other reliability mechanisms baked into the code:

| Mechanism | Where | What it prevents |
|---|---|---|
| Idempotency keys on every write | `tools/executor.py` | Duplicate contacts/events on retry or replay |
| Retry with backoff on 429/5xx | `tools/executor.py` | Transient API failures becoming silent drops |
| Step cap per agent | `agents/base.py` | Runaway tool-calling loops |
| Dry-run mode | `DRY_RUN=1` | Testing against live accounts with zero writes |
| Email-ID dedupe + state check | `orchestrator/machine.py` | Reprocessing the same email; double-booking on double-click |

---

## Project layout

```
server/                  FastAPI backend — agents, orchestrator, tool executor, integrations
  agents/                Router, Extractor, Critic, CRMAgent, Scheduler (agents/base.py runs the LLM loop)
  orchestrator/          states.py (transition table), machine.py (drives runs), registry.py (tool ACLs)
  tools/                 executor.py (single choke point for every tool call), schemas.py
  integrations/          Live + fake Gmail, Calendar, Slack, HubSpot/Airtable, status probes
  store/                 Postgres-backed DB (runs, agent_calls, actions, idempotency cache, eval history)
  evals/                 25-case eval suite (fakes + real LLM)
  server.py              FastAPI app: Slack webhook, /ingest, dashboard API
  tests_smoke.py         Zero-token orchestration tests (stubbed agents)
webapp/                  Next.js dashboard (live run feed, agent registry, escalations, integrations, evals)
docker-compose.yml       Postgres + server + webapp
Makefile                 Convenience targets (make up, make dev-server, make evals, ...)
```

---

## Quickstart

```bash
git clone <this-repo>
cd multi-app-agent-hackathon

make setup      # copies server/.env.example -> server/.env, webapp/.env.example -> webapp/.env.local
# edit server/.env — at minimum set GEMINI_API_KEY (see Configuration below)

make up          # docker compose: postgres + server (:8000) + webapp (:3000)
```

Open **http://localhost:3000**. By default `USE_FAKES=1`, so the whole pipeline runs against in-memory fake Gmail/CRM/Slack/Calendar — no external accounts needed to see it work end to end.

To go live (real Gmail, HubSpot, Slack, Calendar), configure the credentials below, set `USE_FAKES=0`, and restart.

---

## Configuration

All server config lives in `server/.env` (copy from `server/.env.example`). Key switches:

```bash
USE_FAKES=1          # 1 = in-memory fakes for every app, 0 = live integrations
DRY_RUN=0            # 1 = never actually execute writes (log only), useful against live accounts
FAST_MODEL=gemini-3.5-flash-lite   # router + critic
SMART_MODEL=gemini-3.8-flash       # extractor + crm + scheduler
CRM_PROVIDER=hubspot # or airtable
POLL=1               # background thread polls Gmail every 30s (only relevant with USE_FAKES=0)
FRONTEND_ORIGIN=http://localhost:3000
```

The webapp reads `NEXT_PUBLIC_API_URL` from `webapp/.env.local` (default `http://127.0.0.1:8000`). Use `127.0.0.1`, not `localhost` — on macOS `localhost` can resolve to IPv6 and hit a different process than the one you think is on port 8000 (e.g. an old Docker container).

### Gemini API key

1. Go to **[Google AI Studio](https://aistudio.google.com/app/apikey)**.
2. Sign in and click **Create API key**.
3. Copy the key into `server/.env`:
   ```bash
   GEMINI_API_KEY=your-key-here
   ```

This is required even in `USE_FAKES=1` mode, since the LLM agents (router, extractor, critic, CRM, scheduler) always call Gemini — only the *app* integrations (Gmail/CRM/Slack/Calendar) are faked.

### HubSpot private app token

This project uses the HubSpot developer platform / CLI project flow (`hs project` / `app-hsmeta.json`, e.g. a "Get Started" or Auto Deploy–linked app — see [HubSpot Developer Documentation](https://developers.hubspot.com/docs)):

1. Install the CLI and authorize your account:
   ```bash
   npm install -g @hubspot/cli && hs init
   ```
2. In the project, open the app's `app-hsmeta.json` and add the deals scopes to `requiredScopes`:
   ```json
   {
     "uid": "get_started_app",
     "type": "app",
     "config": {
       "auth": {
         "type": "static",
         "requiredScopes": [
           "oauth",
           "crm.objects.contacts.read",
           "crm.objects.contacts.write",
           "crm.objects.deals.read",
           "crm.objects.deals.write"
         ]
       }
     }
   }
   ```
3. Deploy the change — `hs project upload`, or push to whatever branch the project's **Auto Deploy** watches.
4. **Reinstall the app.** This is the step that's easy to miss: a static-token app's *installed* token does **not** automatically pick up new scopes just because `app-hsmeta.json` deployed successfully. HubSpot shows a note on the app's page — *"If you update the app's scopes, you'll need to reinstall the app for the changes to take effect."* Go to the app's install/auth page and reinstall — you'll see a consent screen listing the new permissions (e.g. "Manage and view your CRM data: contacts... and deals...") — approve it to get a token that actually carries the new scopes.
5. Copy the freshly issued token into `server/.env`:
   ```bash
   HUBSPOT_TOKEN=pat-xxxxxxxxxxxxxxxxxxxxxxx
   CRM_PROVIDER=hubspot
   ```

**Important:** simply **regenerating** an existing token after adding scopes is **not** enough for this type of app — **reinstalling** (re-authorizing) is what actually grants the new scopes to the token. A `403 Forbidden` on `create_crm_deal` with a message like `Add scopes: crm.objects.deals.read and crm.objects.deals.write` means the token currently in `.env` still doesn't carry those scopes — check that `app-hsmeta.json` was deployed *and* the app was reinstalled, then update `HUBSPOT_TOKEN` and **restart uvicorn** to pick up the new value.

**No HubSpot account?** Use Airtable instead — set `CRM_PROVIDER=airtable`, plus:
```bash
AIRTABLE_TOKEN=your-airtable-pat
AIRTABLE_BASE=your-base-id
```
with tables `Contacts(Email, Name, Company, Deals)` and `Deals(Title, Contact, Stage)`.

### Slack app tokens

1. Go to **[api.slack.com/apps](https://api.slack.com/apps) → Create New App → From scratch**.
2. Under **OAuth & Permissions**, add Bot Token Scope **`chat:write`**.
3. **Install to workspace**, then copy the **Bot User OAuth Token** (`xoxb-...`).
4. Under **Basic Information → App Credentials**, copy the **Signing Secret**.
5. Invite the bot to the channel you want approvals posted to, then copy that channel's ID (right-click the channel → View channel details → Channel ID, or use `#channel-name` if your Slack client shows it).
6. Fill in `server/.env`:
   ```bash
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_SIGNING_SECRET=...
   SLACK_CHANNEL_ID=C0XXXXXXX
   ```
7. Under **Interactivity & Shortcuts**, turn it **On** and set the **Request URL** to:
   ```
   https://<your-public-url>/slack/interact
   ```
   (see [Exposing Slack interactivity with ngrok](#exposing-slack-interactivity-with-ngrok) below — Slack needs a public HTTPS URL, not `localhost`).

### Google OAuth credentials (Gmail + Calendar)

This app uses a **Desktop app OAuth client**, not a service account.

1. Go to **[Google Cloud Console](https://console.cloud.google.com/)** → create or select a project.
2. **APIs & Services → Library** → enable **Gmail API** and **Google Calendar API**.
3. **APIs & Services → OAuth consent screen** → set it up (External is fine for testing) → add your Gmail account under **Test users**.
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
   - Application type: **Desktop app** (not "Web application", not a service account).
5. Download the JSON and save it as:
   ```
   server/credentials.json
   ```
   It must contain an `"installed"` key — if it contains `"type": "service_account"`, you downloaded the wrong kind of credential and Gmail/Calendar will fail with `ValueError: Client secrets must be for a web or installed app.`
6. Set `USE_FAKES=0` and start the server (see below). The **first** run opens a browser window for you to consent; after that, a `server/token.json` is written and reused automatically — you won't be prompted again unless you delete it.

Both `credentials.json` and `token.json` are git-ignored — never commit them.

---

## Running it

### Option A: Docker Compose

```bash
make setup   # first time only
make up      # builds + starts postgres, server, webapp
make logs    # tail all logs
make down    # stop (keeps postgres data)
```

- Webapp: http://localhost:3000
- API: http://localhost:8000
- Postgres: localhost:5432 (`leadtriage` / `leadtriage`)

The `server` service in `docker-compose.yml` mounts `./server:/app`, so it picks up your local `credentials.json` / `token.json` for Google OAuth and reflects code changes without a rebuild (restart the container to pick up code changes; rebuild only when `requirements.txt` changes).

### Option B: run locally with `make`

Useful when you want fast reload on the API and don't need Docker for the server itself.

```bash
make setup
pip install -r server/requirements.txt
cd webapp && yarn install && cd ..

make postgres      # starts only the Postgres container
make dev-server    # uvicorn --reload on 127.0.0.1:8000
make dev-web       # Next.js dev server on :3000, in another terminal
```

If a Docker `server` container is also running and holding port 8000, stop it first:
```bash
make stop-server
```

### Option C: run manually

```bash
docker compose up -d postgres

cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # fill in GEMINI_API_KEY at minimum
uvicorn server:app --host 127.0.0.1 --port 8000
```

```bash
cd webapp
cp .env.example .env.local
yarn install
yarn dev
```

Other one-off commands:

```bash
python tests_smoke.py        # 0 tokens: orchestration, registry, idempotency, retry, dry-run
python -m evals.run_evals    # fakes + real Gemini calls: 25 cases, prints pass table
python demo.py inject        # rehearse demo beats with fakes
```

---

## Testing without live integrations

Leave `USE_FAKES=1` (the default) to exercise the entire pipeline — Router → Extractor → Critic → CRM → Slack approval → Scheduler — against in-memory fakes. No Gmail, HubSpot, or Slack account required; you still need a **Gemini API key**, since the agents themselves are real.

From the webapp, click **New run**. With fakes, it opens a **"Simulate test email"** form — fill in `From` / `Subject` / `Body` and submit; this posts to `POST /ingest`.

With live Gmail connected (`USE_FAKES=0`), **New run** instead calls `POST /ingest/gmail`, which pulls unread messages from your **Inbox** (`is:unread in:inbox`) and queues them automatically — no form needed. Good test emails look like a real B2B inbound lead:

> Subject: Demo request
> Body: Hi, I lead ops at Acme Corp. We're evaluating tools for our sales team of 40. Could we do a demo next week? Thanks, Jane

Newsletters, vendor pitches, and internal mail are classified `not_lead` and terminate immediately with no CRM/Slack activity — that's expected, not a bug.

Approve/reject a pending run without Slack:
```bash
curl -X POST http://localhost:8000/approve/<run_id>/approve
curl -X POST http://localhost:8000/approve/<run_id>/reject
```

---

## Exposing Slack interactivity with ngrok

Slack's Interactivity Request URL must be a public HTTPS endpoint, so for local dev you need a tunnel:

```bash
# with the API already running on 127.0.0.1:8000
ngrok http 127.0.0.1:8000
```

Take the `https://....ngrok-free.app` URL ngrok prints and set it as the **Request URL** in your Slack app under **Interactivity & Shortcuts**, appending `/slack/interact`:

```
https://<your-subdomain>.ngrok-free.app/slack/interact
```

If you see `502 Bad Gateway` in the ngrok logs, ngrok can't reach anything — confirm uvicorn is actually running on the exact host:port you tunneled (`127.0.0.1:8000`), and that `curl http://127.0.0.1:8000/health` returns `{"ok":true}` locally first.

---

## Useful endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/ingest` | Manually queue one email (JSON body: `id`, `from`, `subject`, `body`) — works with fakes or live |
| `POST` | `/ingest/gmail` | Pull unread inbox mail from the connected Gmail account and queue runs |
| `POST` | `/approve/{run_id}/{decision}` | Approve/reject a run without Slack (`decision` = `approve` or `reject`) |
| `POST` | `/slack/interact` | Slack Interactivity webhook (button clicks) |
| `GET` | `/runs` | Live run feed for the dashboard |
| `GET` | `/runs/{run_id}` | Full trace: agent calls, tool actions, latencies, tokens |
| `GET` | `/escalations` | Runs awaiting human review or quarantined |
| `GET` | `/agents` | Agent registry: role, model, tools, runs today |
| `GET` | `/integrations` | Live connection status for Gmail, CRM, Slack, Calendar |
| `GET` | `/evals` | Latest eval suite results |
| `GET` | `/health` | Liveness check |

---

## Troubleshooting

- **`ValueError: Client secrets must be for a web or installed app`** — your `credentials.json` is a service-account key, not a Desktop OAuth client. Re-download from Google Cloud Console using **Create Credentials → OAuth client ID → Desktop app**.
- **`403 Forbidden` on `create_crm_deal`** — the HubSpot token predates the deals scopes. Add scopes on the private app, **regenerate the token**, update `HUBSPOT_TOKEN`, restart the server. Check `/integrations` — it reports missing HubSpot scopes directly.
- **`AssertionError: The python-multipart library must be installed`** on Slack button clicks — install it: `pip install python-multipart` (already in `requirements.txt`; re-run `pip install -r requirements.txt` if you're on an older checkout).
- **404 on `/ingest/gmail` from the webapp but the route exists in code** — you're hitting a stale server process (often an old Docker container still bound to port 8000). Check `curl http://127.0.0.1:8000/openapi.json` for the route, and use `make stop-server` / rebuild if it's missing.
- **Slack sends to `/slack/interactions` (with an "s")** — the server accepts both `/slack/interact` and `/slack/interactions`; either is fine.
- **`poll error Unable to find the server at gmail.googleapis.com`** — the background Gmail poller (`POLL=1`) can't reach Google; check network/DNS. Set `POLL=0` to stop it while debugging and sync manually via `POST /ingest/gmail` instead.
- **Live feed looks empty or shows an old test run** — the dashboard filters out fixtures from `server/evals/cases/*.json` automatically. If a stray run lingers, check `GET /runs/{id}` for its `context.source` field.
