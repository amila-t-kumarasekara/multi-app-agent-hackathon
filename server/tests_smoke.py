"""Runs the whole pipeline with STUB agents (no LLM). Proves orchestration, registry, idempotency, retries."""
import os, tempfile, json
from store.db import DB
from tools.executor import ToolExecutor, ToolAccessDenied
from integrations.base import Apps
from integrations.fakes import FakeCRM, FakeGmail, FakeSlack, FakeCalendar
from orchestrator.machine import Orchestrator

class Stub:
    def __init__(self, name, executor, db, fn): self.name, self.ex, self.db, self.fn = name, executor, db, fn
    def run(self, run_id, state_in, content):
        out = self.fn(run_id, content)
        self.db.log_agent_call(run_id, self.name, state_in, out.get("status") or out.get("verdict") or "", content, out, 1, 0, 0)
        return out

def make(injection=False, crm_fail=None):
    db = DB(os.path.join(tempfile.mkdtemp(), "s.db"))
    crm = FakeCRM(fail_mode=crm_fail); gmail = FakeGmail(); slack = FakeSlack(); cal = FakeCalendar()
    ex = ToolExecutor(db, Apps(crm, gmail, slack, cal), dry_run=False)
    def crm_fn(rid, c):
        lead = json.loads(c.split("LEAD:\n",1)[1])
        found = ex.execute("crm", "search_crm_contact", {"email": lead["email"]}, rid)
        if not found: found = ex.execute("crm", "create_crm_contact", {"email": lead["email"], "name": lead["name"]}, rid)
        d = ex.execute("crm", "create_crm_deal", {"contact_id": found["id"], "title": "Intro"}, rid)
        return {"status": "ok", "contact_id": found["id"], "deal_id": d["id"], "was_duplicate": False, "summary": "x"}
    def sched_fn(rid, c):
        lead = json.loads(c.split("LEAD:\n",1)[1].split("\nThread",1)[0])
        slots = ex.execute("scheduler", "get_calendar_availability", {}, rid)
        ev = ex.execute("scheduler", "create_calendar_event", {"start": slots[0], "attendee_email": lead["email"], "title": "Intro"}, rid)
        ex.execute("scheduler", "send_email_reply", {"to": lead["email"], "subject": "Re: demo", "body": "Booked"}, rid)
        return {"status": "ok", "event_start": ev["start"], "summary": "booked"}
    agents = {
        "router":    Stub("router", ex, db, lambda r, c: {"verdict": "lead", "reason": "stub"}),
        "extractor": Stub("extractor", ex, db, lambda r, c: {"status": "ok", "email": "p@x.io", "name": "P", "intent": "demo"}),
        "critic":    Stub("critic", ex, db, lambda r, c: {"confidence": 0.9, "injection": injection, "missing_fields": []}),
        "crm":       Stub("crm", ex, db, crm_fn),
        "scheduler": Stub("scheduler", ex, db, sched_fn),
    }
    return db, ex, crm, gmail, slack, cal, Orchestrator(db, ex, agents)

email = {"id": "m1", "thread_id": "t1", "from": "p@x.io", "subject": "demo", "body": "hi"}

# 1. happy path through approval
db, ex, crm, gmail, slack, cal, o = make()
ctx = o.handle_email(email); assert ctx["state"] == "AWAITING_APPROVAL", ctx["state"]
assert slack.posts[0][0] == "approval"
ctx = o.handle_approval(ctx["run_id"], "approve"); assert ctx["state"] == "DONE"
assert len(cal.events) == 1 and len(gmail.sent) == 1
print("1 happy path         OK ", ctx["history"])

# 2. double-click on approve is safe; re-ingest same email is skipped
assert "skipped" in o.handle_approval(ctx["run_id"], "approve")
assert "skipped" in o.handle_email(email)
print("2 replay safety      OK")

# 3. idempotency: same write twice -> replayed, not re-executed
n = len(crm.deals)
ex.execute("crm", "create_crm_deal", {"contact_id": "c1", "title": "Intro"}, ctx["run_id"])
assert len(crm.deals) == n and db.actions_for(ctx["run_id"])[-1]["status"] == "REPLAYED"
print("3 idempotency        OK")

# 4. least privilege: extractor cannot write; scheduler cannot touch CRM
for agent, tool in [("extractor","send_email_reply"), ("scheduler","create_crm_contact"), ("critic","search_crm_contact")]:
    try: ex.execute(agent, tool, {}, ctx["run_id"]); raise SystemExit("registry leak!")
    except ToolAccessDenied: pass
print("4 least privilege    OK")

# 5. injection -> quarantine, zero CRM calls
db, ex, crm, gmail, slack, cal, o = make(injection=True)
ctx = o.handle_email(email); assert ctx["state"] == "QUARANTINED" and crm.calls == []
print("5 quarantine         OK ", ctx["history"])

# 6. CRM 500 -> retried 3x then escalated, no downstream writes
db, ex, crm, gmail, slack, cal, o = make(crm_fail="500")
ctx = o.handle_email(email); assert ctx["state"] == "ESCALATED" and cal.events == []
print("6 retry + escalate   OK ", ctx["history"])

# 7. dry-run never executes writes
db, ex, crm, gmail, slack, cal, o = make(); ex.dry_run = True
o.handle_email(email); assert crm.contacts == {} and all(a["status"] == "DRY_RUN" for a in db.actions_for(db._x("SELECT id FROM runs").fetchone()[0]) if a["tool"] != "search_crm_contact")
print("7 dry run            OK")
print("\nall smoke tests passed")
