"""End-to-end + per-agent evals against fakes. Usage: python -m evals.run_evals [--live-llm]"""
import json, glob, os, sys, time
from store.db import DB
from tools.executor import ToolExecutor
from integrations.base import Apps
from integrations.fakes import FakeCRM, FakeGmail, FakeSlack, FakeCalendar
from orchestrator.machine import Orchestrator

def build(case, db):
    st = case.get("app_state", {}); faults = case.get("faults", {})
    crm = FakeCRM(st.get("crm_contacts"), fail_mode=faults.get("crm"))
    gmail = FakeGmail(fail_send=faults.get("gmail_send", False))
    slack = FakeSlack(timeout=faults.get("slack_timeout", False))
    cal = FakeCalendar(all_busy=faults.get("calendar_busy", False))
    db.reset()
    ex = ToolExecutor(db, Apps(crm, gmail, slack, cal), dry_run=False)
    return db, ex, crm, gmail, slack, cal

def check(exp, ctx, db, crm, gmail, cal):
    fails = []
    if "final_state" in exp and ctx["state"] != exp["final_state"]:
        fails.append(f"state {ctx['state']} != {exp['final_state']}")
    tools_called = [a["tool"] for a in db.actions_for(ctx["run_id"]) if a["status"] in ("OK", "REPLAYED")]
    for t in exp.get("must_call", []):
        if t not in tools_called: fails.append(f"missing call {t}")
    for t in exp.get("must_not_call", []):
        if t in tools_called: fails.append(f"forbidden call {t}")
    if "max_contacts_created" in exp and crm.calls.count("create") > exp["max_contacts_created"]:
        fails.append(f"created {crm.calls.count('create')} contacts")
    if "emails_sent" in exp and len(gmail.sent) != exp["emails_sent"]:
        fails.append(f"sent {len(gmail.sent)} emails, expected {exp['emails_sent']}")
    if exp.get("critic_injection") is not None and bool((ctx.get("critique") or {}).get("injection")) != exp["critic_injection"]:
        fails.append("critic injection flag wrong")
    if "router_verdict" in exp and (ctx.get("route") or {}).get("verdict") != exp["router_verdict"]:
        fails.append(f"router said {(ctx.get('route') or {}).get('verdict')}")
    for f, v in exp.get("extraction_fields", {}).items():
        got = (ctx.get("extraction") or {}).get(f)
        if (got or "").lower() != (v or "").lower(): fails.append(f"extraction.{f}={got!r} != {v!r}")
    return fails

def main():
    cases = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "cases", "*.json")))
    shared_db = DB()
    rows, passed = [], 0
    db_rows = []  # (case_id, bucket, result, detail, latency_ms) for persistence
    for path in cases:
        case = json.load(open(path))
        db, ex, crm, gmail, slack, cal = build(case, shared_db)
        orch = Orchestrator(db, ex)
        t0 = time.time()
        try:
            ctx = orch.handle_email(case["email"], source="eval")
            if ctx.get("state") == "AWAITING_APPROVAL" and case.get("approve", True):
                ctx = orch.handle_approval(ctx["run_id"], "approve")
            fails = check(case["expect"], ctx, db, crm, gmail, cal)
        except Exception as e:
            fails = [f"EXCEPTION {e}"]
        latency_ms = int((time.time() - t0) * 1000)
        ok = not fails; passed += ok
        bucket = case.get("bucket", "-")
        detail = "; ".join(fails)
        rows.append((case["id"], bucket, "PASS" if ok else "FAIL", detail, latency_ms))
        db_rows.append((case["id"], bucket, "Pass" if ok else "Fail", detail, latency_ms))
    w = max(len(r[0]) for r in rows)
    print(f"\n{'case':<{w}}  {'bucket':<10} result  latency  detail")
    for r in rows: print(f"{r[0]:<{w}}  {r[1]:<10} {r[2]:<6}  {r[4]:>5}ms  {r[3]}")
    print(f"\n{passed}/{len(rows)} passed ({100*passed//max(1,len(rows))}%)")
    by = {}
    for r in rows: by.setdefault(r[1], [0, 0]); by[r[1]][1] += 1; by[r[1]][0] += r[2] == "PASS"
    for b, (p, n) in sorted(by.items()): print(f"  {b:<12} {p}/{n}")
    shared_db.save_eval_run(passed, len(rows), db_rows)
    sys.exit(0 if passed == len(rows) else 1)

if __name__ == "__main__": main()
