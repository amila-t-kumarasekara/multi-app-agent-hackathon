"""FastAPI: Slack interactivity endpoint (3s ack rule) + manual triggers + run inspection."""
import json, hmac, hashlib, time, os, threading
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from store.db import DB
from tools.executor import ToolExecutor
from integrations.factory import build_apps
from orchestrator.machine import Orchestrator

app = FastAPI()
db = DB(); apps = build_apps(); ex = ToolExecutor(db, apps); orch = Orchestrator(db, ex)

def _verify(req_body: bytes, ts: str, sig: str):
    secret = os.getenv("SLACK_SIGNING_SECRET")
    if not secret: return True
    if abs(time.time() - int(ts)) > 300: return False
    mine = "v0=" + hmac.new(secret.encode(), f"v0:{ts}:{req_body.decode()}".encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(mine, sig)

@app.post("/slack/interact")
async def slack_interact(req: Request, bg: BackgroundTasks):
    body = await req.body()
    if not _verify(body, req.headers.get("X-Slack-Request-Timestamp", "0"), req.headers.get("X-Slack-Signature", "")):
        raise HTTPException(401)
    form = await req.form()
    payload = json.loads(form["payload"])
    action = payload["actions"][0]
    run_id, decision = action["value"], "approve" if action["action_id"] == "approve_lead" else "reject"
    bg.add_task(orch.handle_approval, run_id, decision)      # do the work AFTER we ack
    return JSONResponse({"replace_original": True, "text": f"{'✅ Approved' if decision=='approve' else '⛔ Rejected'} run {run_id} by <@{payload['user']['id']}> — booking…"})

@app.post("/ingest")            # manual trigger for demos / curl
async def ingest(email: dict, bg: BackgroundTasks):
    bg.add_task(orch.handle_email, email); return {"queued": email.get("id")}

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

def poll_loop(interval=30):
    while True:
        try:
            for e in apps.gmail.fetch_unread():
                orch.handle_email(e)
        except Exception as ex_: print("poll error", ex_)
        time.sleep(interval)

if os.getenv("POLL", "0") == "1":
    threading.Thread(target=poll_loop, daemon=True).start()
