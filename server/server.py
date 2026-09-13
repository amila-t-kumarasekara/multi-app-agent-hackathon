"""FastAPI: Slack interactivity endpoint (3s ack rule) + manual triggers + run inspection + dashboard API."""
import json, hmac, hashlib, time, os, threading
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Body
from evals.case_ids import eval_email_ids, is_live_run
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from store.db import DB
from tools.executor import ToolExecutor
from integrations.factory import build_apps
from orchestrator.machine import Orchestrator
from orchestrator.registry import REGISTRY
from config import FRONTEND_ORIGIN, FAST_MODEL, SMART_MODEL
from integrations.status import build_integration_list

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DB(); apps = build_apps(); ex = ToolExecutor(db, apps); orch = Orchestrator(db, ex)

def _verify(req_body: bytes, ts: str, sig: str):
    secret = os.getenv("SLACK_SIGNING_SECRET")
    if not secret: return True
    if abs(time.time() - int(ts)) > 300: return False
    mine = "v0=" + hmac.new(secret.encode(), f"v0:{ts}:{req_body.decode()}".encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(mine, sig)

async def _slack_interact(req: Request, bg: BackgroundTasks):
    body = await req.body()
    if not _verify(body, req.headers.get("X-Slack-Request-Timestamp", "0"), req.headers.get("X-Slack-Signature", "")):
        raise HTTPException(401)
    form = await req.form()
    payload = json.loads(form["payload"])
    action = payload["actions"][0]
    run_id, decision = action["value"], "approve" if action["action_id"] == "approve_lead" else "reject"
    bg.add_task(orch.handle_approval, run_id, decision)      # do the work AFTER we ack
    return JSONResponse({"replace_original": True, "text": f"{'✅ Approved' if decision=='approve' else '⛔ Rejected'} run {run_id} by <@{payload['user']['id']}> — booking…"})

@app.post("/slack/interact")
async def slack_interact(req: Request, bg: BackgroundTasks):
    return await _slack_interact(req, bg)

@app.post("/slack/interactions")
async def slack_interactions_alias(req: Request, bg: BackgroundTasks):
    """Alias for Slack apps configured with /slack/interactions (common typo)."""
    return await _slack_interact(req, bg)

@app.post("/ingest")            # manual trigger for demos / curl / simulate without Gmail
async def ingest(bg: BackgroundTasks, email: dict = Body(...)):
    bg.add_task(orch.handle_email, email, "live")
    return {"queued": email.get("id")}

@app.post("/ingest/gmail")
async def ingest_gmail(bg: BackgroundTasks):
    """Pull unread inbox messages from the connected Gmail account and queue triage runs."""
    from integrations.fakes import FakeGmail
    if isinstance(apps.gmail, FakeGmail):
        raise HTTPException(
            400,
            detail="Gmail is not connected. Complete Google OAuth or use POST /ingest with a test email.",
        )
    unread = apps.gmail.fetch_unread()
    queued = []
    for email in unread:
        if db.seen_email(email["id"]):
            continue
        bg.add_task(orch.handle_email, email, "live")
        queued.append(email["id"])
    if not queued:
        return {
            "queued": [],
            "message": "No new unread messages (already processed or inbox empty).",
        }
    return {"queued": queued, "message": f"Processing {len(queued)} unread email(s)…"}

@app.post("/approve/{run_id}/{decision}")   # local shortcut when Slack isn't wired
async def approve(run_id: str, decision: str):
    return orch.handle_approval(run_id, decision)

@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    r = db.get_run(run_id)
    if not r: raise HTTPException(404)
    return {"run": r, "agent_calls": db.calls_for(run_id), "actions": db.actions_for(run_id)}

@app.get("/health")
async def health(): return {"ok": True}

# ---------------------------------------------------------------------------
# Dashboard API: everything below is read-only data for the webapp frontend.
# ---------------------------------------------------------------------------

STATUS_BY_STATE = {"DONE": "Completed", "ESCALATED": "Escalated", "QUARANTINED": "Escalated", "FAILED": "Failed"}
TAG_CLASS_BY_STATUS = {"Completed": "tag-accent-2", "Escalated": "tag-outline", "Failed": "tag-outline", "Running": "tag-accent"}
STAGE_BY_STATE = {"RECEIVED": 1, "ROUTED": 1, "EXTRACTED": 2, "CRITIQUED": 2,
                  "CRM_SYNCED": 3, "AWAITING_APPROVAL": 3, "SCHEDULED": 4, "DONE": 5}
AGENT_BY_STATE = {"RECEIVED": "router", "ROUTED": "extractor", "EXTRACTED": "critic", "CRITIQUED": "crm",
                  "CRM_SYNCED": "orchestrator", "AWAITING_APPROVAL": "orchestrator",
                  "SCHEDULED": "scheduler", "DONE": "scheduler"}

def _summarize_run(run: dict) -> dict:
    ctx = run["context"]
    email = ctx.get("email") or {}
    extraction = ctx.get("extraction") or {}
    state = run["state"]
    status = STATUS_BY_STATE.get(state, "Running")
    frm = email.get("from", "")
    lead_name = extraction.get("name") or frm.split("<")[0].strip() or frm or "Unknown"
    stage = STAGE_BY_STATE.get(state)
    if stage is None:
        stage = min(len(ctx.get("history") or []), 5)
    return {
        "id": run["id"],
        "emailId": run["email_id"],
        "leadName": lead_name,
        "company": extraction.get("company") or "—",
        "agent": AGENT_BY_STATE.get(state, "orchestrator"),
        "state": state,
        "status": status,
        "tagClass": TAG_CLASS_BY_STATUS[status],
        "stage": stage,
        "createdAt": run["created_at"],
        "updatedAt": run["updated_at"],
        "note": ctx.get("note"),
    }

@app.get("/runs")
async def list_runs(limit: int = 200):
    return [_summarize_run(r) for r in db.list_runs(limit) if is_live_run(r)]

@app.get("/escalations")
async def escalations():
    out = []
    for r in db.runs_in_states(["ESCALATED", "QUARANTINED"]):
        if not is_live_run(r):
            continue
        s = _summarize_run(r)
        s["reason"] = s["note"] or "Escalated for human review"
        s["risk"] = "High" if r["state"] == "QUARANTINED" else "Medium"
        s["riskClass"] = "tag-outline" if s["risk"] == "High" else "tag-accent"
        out.append(s)
    return out

@app.get("/stats")
async def stats():
    s = db.stats(exclude_email_ids=list(eval_email_ids()))
    return {
        "runsToday": s["runs_today"],
        "autoResolvedPct": s["auto_resolved_pct"],
        "inEscalation": s["in_escalation"],
        "avgFirstActionS": (s["avg_first_action_ms"] or 0) / 1000,
    }

TOOL_ICON = {
    "search_crm_contact": "database", "create_crm_contact": "database",
    "update_crm_contact": "database", "create_crm_deal": "database",
    "get_calendar_availability": "calendar", "create_calendar_event": "calendar",
    "send_email_reply": "mail",
    "post_slack_approval": "message", "post_slack_message": "message",
}
AGENT_META = {
    "router":       {"role": "Classifies inbound email as lead / not-lead / ambiguous. No tool access.", "model": FAST_MODEL},
    "extractor":    {"role": "Extracts structured lead fields from the email. No tool access.", "model": SMART_MODEL},
    "critic":       {"role": "Audits extraction confidence and screens for prompt injection. No tool access.", "model": FAST_MODEL},
    "crm":          {"role": "Syncs the qualified lead into the CRM.", "model": SMART_MODEL},
    "scheduler":    {"role": "Books the intro call and confirms by email.", "model": SMART_MODEL},
    "orchestrator": {"role": "Posts Slack approval cards and alerts. Table-driven, no LLM.", "model": "—"},
}

@app.get("/agents")
async def agents():
    out = []
    for name, tools in REGISTRY.items():
        meta = AGENT_META.get(name, {"role": "", "model": "—"})
        out.append({
            "name": name,
            "role": meta["role"],
            "model": meta["model"],
            "status": "Active",
            "statusClass": "tag-accent-2",
            "runsToday": db.agent_runs_today(name),
            "tools": sorted({TOOL_ICON[t] for t in tools}),
        })
    return out

@app.get("/integrations")
async def integrations():
    return build_integration_list(apps)

@app.get("/evals")
async def evals():
    latest = db.latest_eval()
    if not latest:
        return None
    run, cases = latest["run"], latest["cases"]
    total = run["total"] or 1
    pass_rate = run["passed"] / total * 100
    buckets = sorted({c["bucket"] for c in cases})
    latencies = [c["latency_ms"] for c in cases if c["latency_ms"] is not None]
    avg_latency_s = (sum(latencies) / len(latencies) / 1000) if latencies else 0
    metrics = [
        {"label": "Overall pass rate", "value": f"{pass_rate:.1f}%",
         "trend": f"{run['passed']}/{run['total']} cases", "up": pass_rate >= 90},
        {"label": "Buckets covered", "value": str(len(buckets)), "trend": ", ".join(buckets), "up": True},
        {"label": "Avg case latency", "value": f"{avg_latency_s:.1f}s",
         "trend": f"{len(cases)} cases timed", "up": True},
        {"label": "Last run", "value": time.strftime("%H:%M:%S", time.localtime(run["created_at"])),
         "trend": time.strftime("%Y-%m-%d", time.localtime(run["created_at"])), "up": True},
    ]
    case_rows = [
        {"name": c["case_id"], "category": c["bucket"], "result": c["result"],
         "latency": f"{(c['latency_ms'] or 0) / 1000:.1f}s"}
        for c in cases
    ]
    return {"metrics": metrics, "cases": case_rows}

def poll_loop(interval=30):
    while True:
        try:
            for e in apps.gmail.fetch_unread():
                orch.handle_email(e)
        except Exception as ex_: print("poll error", ex_)
        time.sleep(interval)

if os.getenv("POLL", "0") == "1":
    threading.Thread(target=poll_loop, daemon=True).start()
