"""Single choke point for every tool call.
Enforces: agent tool-access, idempotency, retry with backoff, dry-run, full audit log."""
import hashlib, json, time
from orchestrator.registry import REGISTRY, WRITE_TOOLS
from config import DRY_RUN

class ToolAccessDenied(Exception): pass
class ToolFailed(Exception): pass

RETRYABLE = (429, 500, 502, 503, 504)

class ToolExecutor:
    def __init__(self, db, apps, dry_run=DRY_RUN):
        self.db, self.apps, self.dry_run = db, apps, dry_run
        self.dispatch = {
            "search_crm_contact":        lambda a: apps.crm.search(a["email"]),
            "create_crm_contact":        lambda a: apps.crm.create(a),
            "update_crm_contact":        lambda a: apps.crm.update(a["contact_id"], a["fields"]),
            "create_crm_deal":           lambda a: apps.crm.create_deal(a),
            "get_calendar_availability": lambda a: apps.calendar.free_slots(a.get("preferred")),
            "create_calendar_event":     lambda a: apps.calendar.create_event(a),
            "send_email_reply":          lambda a: apps.gmail.send(a),
            "post_slack_approval":       lambda a: apps.slack.post_approval(a),
            "post_slack_message":        lambda a: apps.slack.post_message(a),
        }

    @staticmethod
    def idem_key(run_id, tool, args):
        raw = f"{run_id}|{tool}|{json.dumps(args, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

    def execute(self, agent, tool, args, run_id):
        # 1. least privilege
        if tool not in REGISTRY.get(agent, set()):
            self.db.log_action(run_id, agent, tool, args, {"error": "access_denied"}, "DENIED", None)
            raise ToolAccessDenied(f"{agent} may not call {tool}")

        is_write = tool in WRITE_TOOLS
        key = self.idem_key(run_id, tool, args) if is_write else None

        # 2. idempotency: replay returns cached result
        if key and (cached := self.db.idem_get(key)) is not None:
            self.db.log_action(run_id, agent, tool, args, cached, "REPLAYED", key)
            return cached

        # 3. dry run: never touch a live write
        if is_write and self.dry_run:
            res = {"dry_run": True, "tool": tool, "args": args}
            self.db.log_action(run_id, agent, tool, args, res, "DRY_RUN", key)
            return res

        # 4. retry with backoff on transient failures
        last = None
        for attempt in range(3):
            try:
                res = self.dispatch[tool](args)
                self.db.log_action(run_id, agent, tool, args, res, "OK", key)
                if key: self.db.idem_put(key, res)
                return res
            except TransientError as e:
                last = e; time.sleep(0.5 * (2 ** attempt))
            except Exception as e:
                self.db.log_action(run_id, agent, tool, args, {"error": str(e)}, "FAILED", key)
                raise ToolFailed(str(e))
        self.db.log_action(run_id, agent, tool, args, {"error": str(last)}, "FAILED_RETRIES", key)
        raise ToolFailed(f"{tool} failed after retries: {last}")

class TransientError(Exception):
    """Raise from integrations on 429/5xx/timeouts to trigger retry."""
