"""Deterministic orchestrator. Routes between agents by table; never by LLM."""
import json, uuid
from orchestrator.states import State, next_state, TERMINAL
from agents.router import Router
from agents.extractor import Extractor
from agents.critic import Critic
from agents.crm_agent import CRMAgent
from agents.scheduler import Scheduler
from config import CRITIC_THRESHOLD

class Orchestrator:
    def __init__(self, db, executor, agents=None):
        self.db, self.ex = db, executor
        a = agents or {}
        self.router    = a.get("router")    or Router(executor, db)
        self.extractor = a.get("extractor") or Extractor(executor, db)
        self.critic    = a.get("critic")    or Critic(executor, db)
        self.crm       = a.get("crm")       or CRMAgent(executor, db)
        self.scheduler = a.get("scheduler") or Scheduler(executor, db)

    def _advance(self, ctx, event):
        ctx["state"] = next_state(State(ctx["state"]), event).value
        ctx["history"].append(ctx["state"])
        self.db.update_run(ctx["run_id"], ctx["state"], ctx)

    def _call(self, agent, ctx, content):
        """An agent crashing is an 'error' event, never an unhandled exception."""
        try: return agent.run(ctx["run_id"], ctx["state"], content)
        except Exception as e: return {"status": "error", "reason": f"{agent.name} crashed: {e}"}

    def _slack(self, ctx, tool, args):
        try: return self.ex.execute("orchestrator", tool, args, ctx["run_id"])
        except Exception as e: return {"error": str(e)}

    # ---- entry point 1: new email -------------------------------------------
    def handle_email(self, email: dict, source: str = "live") -> dict:
        if self.db.seen_email(email["id"]):
            return {"skipped": "already_processed", "email_id": email["id"]}
        run_id = str(uuid.uuid4())[:8]
        ctx = {"run_id": run_id, "email": email, "state": State.RECEIVED.value,
               "history": [State.RECEIVED.value], "extraction": None, "critique": None, "crm": None,
               "source": source}
        self.db.create_run(run_id, email["id"], ctx["state"], ctx)
        try:
            return self._process(ctx)
        except Exception as e:
            ctx["error"] = str(e); ctx["state"] = State.FAILED.value
            self.db.update_run(run_id, ctx["state"], ctx)
            self._slack(ctx, "post_slack_message", {"text": f":x: run {run_id} failed: {e}"})
            return ctx

    def _process(self, ctx):
        email_text = f"From: {ctx['email']['from']}\nSubject: {ctx['email']['subject']}\n\n{ctx['email']['body']}"

        # RECEIVED -> Router
        r = self._call(self.router, ctx, email_text)
        ctx["route"] = r
        self._advance(ctx, r.get("verdict") if r.get("verdict") in ("lead","not_lead","ambiguous") else "ambiguous")
        if ctx["state"] in TERMINAL: return self._finish(ctx, f"router: {r.get('reason')}")

        # ROUTED -> Extractor
        x = self._call(self.extractor, ctx, email_text)
        ctx["extraction"] = x
        self._advance(ctx, "ok" if x.get("status") == "ok" and x.get("email") else "error")
        if ctx["state"] in TERMINAL: return self._finish(ctx, "extraction failed")

        # EXTRACTED -> Critic
        c = self._call(self.critic, ctx,
                            f"RAW EMAIL:\n{email_text}\n\nEXTRACTION:\n{json.dumps(x)}")
        ctx["critique"] = c
        if c.get("injection"):            ev = "injection"
        elif float(c.get("confidence", 0)) < CRITIC_THRESHOLD: ev = "low_confidence"
        else:                             ev = "pass"
        self._advance(ctx, ev)
        if ctx["state"] in TERMINAL: return self._finish(ctx, f"critic: {ev} — {c.get('injection_reason') or c.get('notes')}")

        # CRITIQUED -> CRM agent
        k = self._call(self.crm, ctx, f"LEAD:\n{json.dumps(x)}")
        ctx["crm"] = k
        self._advance(ctx, "ok" if k.get("status") == "ok" else "error")
        if ctx["state"] in TERMINAL: return self._finish(ctx, f"crm: {k.get('reason')}")

        # CRM_SYNCED -> post approval card, wait
        self._slack(ctx, "post_slack_approval", {
            "run_id": ctx["run_id"], "lead": x, "crm": k,
            "confidence": c.get("confidence")})
        self._advance(ctx, "ok")
        return ctx

    # ---- entry point 2: Slack button ----------------------------------------
    def handle_approval(self, run_id, decision: str) -> dict:
        run = self.db.get_run(run_id)
        if not run: return {"error": "unknown run"}
        ctx = run["context"]
        if ctx["state"] != State.AWAITING_APPROVAL.value:
            return {"skipped": f"run in state {ctx['state']}"}   # double-click safe
        self._advance(ctx, decision)
        if decision == "reject": return self._finish(ctx, "rejected by human")
        x = ctx["extraction"]
        s = self._call(self.scheduler, ctx,
            f"LEAD:\n{json.dumps(x)}\nThread subject: {ctx['email']['subject']}")
        ctx["schedule"] = s
        self._advance(ctx, "ok" if s.get("status") == "ok" else "error")
        return self._finish(ctx, s.get("summary") or s.get("reason"))

    # ---- entry point 3: escalation / quarantine queue -----------------------
    def handle_escalation_review(self, run_id, decision: str) -> dict:
        run = self.db.get_run(run_id)
        if not run:
            return {"error": "unknown run"}
        ctx = run["context"]
        if ctx["state"] not in (State.ESCALATED.value, State.QUARANTINED.value):
            return {"skipped": f"run in state {ctx['state']}"}
        if decision == "reject":
            ctx["state"] = State.DONE.value
            ctx["history"].append(State.DONE.value)
            return self._finish(ctx, "dismissed by human")
        return self._resume_after_human_review(ctx)

    def _resume_after_human_review(self, ctx):
        """Human approved an escalated/quarantined run — continue (or retry) the pipeline."""
        email_text = (
            f"From: {ctx['email']['from']}\nSubject: {ctx['email']['subject']}\n\n{ctx['email']['body']}"
        )
        x = ctx.get("extraction")

        if not x or x.get("status") != "ok" or not x.get("email"):
            if ctx["state"] == State.ESCALATED.value and State.ROUTED.value not in ctx["history"]:
                ctx["state"] = State.RECEIVED.value
                ctx["route"] = ctx.get("route") or {"verdict": "lead", "reason": "human override"}
                self._advance(ctx, "lead")
            x = self._call(self.extractor, ctx, email_text)
            ctx["extraction"] = x
            self._advance(ctx, "ok" if x.get("status") == "ok" and x.get("email") else "error")
            if ctx["state"] in TERMINAL:
                return self._finish(ctx, "extraction failed after human review")

        x = ctx["extraction"]

        if ctx["state"] in (State.ESCALATED.value, State.QUARANTINED.value, State.EXTRACTED.value):
            ctx["state"] = State.CRITIQUED.value
            if not ctx["history"] or ctx["history"][-1] != State.CRITIQUED.value:
                ctx["history"].append(State.CRITIQUED.value)

        k = self._call(self.crm, ctx, f"LEAD:\n{json.dumps(x)}")
        ctx["crm"] = k
        self._advance(ctx, "ok" if k.get("status") == "ok" else "error")
        if ctx["state"] in TERMINAL:
            return self._finish(ctx, f"crm: {k.get('reason')}")

        self._slack(ctx, "post_slack_approval", {
            "run_id": ctx["run_id"], "lead": x, "crm": k,
            "confidence": (ctx.get("critique") or {}).get("confidence")})
        self._advance(ctx, "ok")
        self.db.update_run(ctx["run_id"], ctx["state"], ctx)
        return ctx

    def _finish(self, ctx, note):
        ctx["note"] = note
        self.db.update_run(ctx["run_id"], ctx["state"], ctx)
        if ctx["state"] in (State.ESCALATED.value, State.QUARANTINED.value):
            icon = ":rotating_light:" if ctx["state"] == "QUARANTINED" else ":warning:"
            self._slack(ctx, "post_slack_message",
                {"text": f"{icon} run {ctx['run_id']} {ctx['state']}: {note}\nFrom: {ctx['email']['from']} — {ctx['email']['subject']}"})
        return ctx
