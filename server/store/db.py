"""Postgres state: runs, agent_calls, actions, idempotency cache, eval history."""
import json, time, threading
import psycopg2
import psycopg2.extras
from config import DATABASE_URL

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY, email_id TEXT UNIQUE, state TEXT, context TEXT,
  created_at DOUBLE PRECISION, updated_at DOUBLE PRECISION);
CREATE TABLE IF NOT EXISTS agent_calls (
  id SERIAL PRIMARY KEY, run_id TEXT, agent TEXT,
  state_in TEXT, state_out TEXT, input TEXT, output TEXT,
  latency_ms INTEGER, tokens_in INTEGER, tokens_out INTEGER, created_at DOUBLE PRECISION);
CREATE TABLE IF NOT EXISTS actions (
  id SERIAL PRIMARY KEY, run_id TEXT, agent TEXT, tool TEXT,
  args TEXT, result TEXT, status TEXT, idem_key TEXT, created_at DOUBLE PRECISION);
CREATE TABLE IF NOT EXISTS idem (
  key TEXT PRIMARY KEY, result TEXT, created_at DOUBLE PRECISION);
CREATE TABLE IF NOT EXISTS eval_runs (
  id SERIAL PRIMARY KEY, created_at DOUBLE PRECISION, passed INTEGER, total INTEGER);
CREATE TABLE IF NOT EXISTS eval_cases (
  id SERIAL PRIMARY KEY, eval_run_id INTEGER REFERENCES eval_runs(id) ON DELETE CASCADE,
  case_id TEXT, bucket TEXT, result TEXT, detail TEXT, latency_ms INTEGER);
"""

class DB:
    def __init__(self, dsn=DATABASE_URL):
        self.conn = psycopg2.connect(dsn)
        self.conn.autocommit = False
        with self.conn.cursor() as cur:
            cur.execute(SCHEMA)
        self.conn.commit()

    def _x(self, sql, params=()):
        with _lock:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, params)
            self.conn.commit()
            return cur

    def reset(self):
        """Wipe all tables. Used to isolate test/eval runs against the shared Postgres instance."""
        with _lock:
            with self.conn.cursor() as cur:
                cur.execute("TRUNCATE runs, agent_calls, actions, idem, eval_runs, eval_cases RESTART IDENTITY CASCADE")
            self.conn.commit()

    # runs
    def create_run(self, run_id, email_id, state, context):
        now = time.time()
        self._x("INSERT INTO runs VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
                (run_id, email_id, state, json.dumps(context), now, now))

    def update_run(self, run_id, state, context):
        self._x("UPDATE runs SET state=%s, context=%s, updated_at=%s WHERE id=%s",
                (state, json.dumps(context), time.time(), run_id))

    def get_run(self, run_id):
        r = self._x("SELECT * FROM runs WHERE id=%s", (run_id,)).fetchone()
        return dict(r, context=json.loads(r["context"])) if r else None

    def list_runs(self, limit=200):
        rows = self._x("SELECT * FROM runs ORDER BY created_at DESC LIMIT %s", (limit,)).fetchall()
        return [dict(r, context=json.loads(r["context"])) for r in rows]

    def runs_in_states(self, states, limit=200):
        rows = self._x("SELECT * FROM runs WHERE state = ANY(%s) ORDER BY updated_at DESC LIMIT %s",
                        (list(states), limit)).fetchall()
        return [dict(r, context=json.loads(r["context"])) for r in rows]

    def seen_email(self, email_id):
        return self._x("SELECT 1 FROM runs WHERE email_id=%s", (email_id,)).fetchone() is not None

    def stats(self):
        today_start = time.time() - (time.time() % 86400)
        runs_today = self._x("SELECT COUNT(*) AS n FROM runs WHERE created_at >= %s", (today_start,)).fetchone()["n"]
        terminal = self._x(
            "SELECT state, COUNT(*) AS n FROM runs WHERE state IN ('DONE','ESCALATED','QUARANTINED','FAILED') GROUP BY state"
        ).fetchall()
        terminal_counts = {r["state"]: r["n"] for r in terminal}
        terminal_total = sum(terminal_counts.values())
        done = terminal_counts.get("DONE", 0)
        auto_resolved_pct = (done / terminal_total * 100) if terminal_total else None
        in_escalation = self._x(
            "SELECT COUNT(*) AS n FROM runs WHERE state IN ('ESCALATED','QUARANTINED')"
        ).fetchone()["n"]
        avg_first_action_ms = self._x(
            "SELECT AVG(latency_ms) AS a FROM agent_calls WHERE agent = 'router'"
        ).fetchone()["a"]
        return {
            "runs_today": runs_today,
            "auto_resolved_pct": auto_resolved_pct,
            "in_escalation": in_escalation,
            "avg_first_action_ms": avg_first_action_ms,
        }

    # observability
    def log_agent_call(self, run_id, agent, s_in, s_out, inp, out, ms, tin, tout):
        self._x("INSERT INTO agent_calls (run_id,agent,state_in,state_out,input,output,latency_ms,tokens_in,tokens_out,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (run_id, agent, s_in, s_out, json.dumps(inp)[:4000], json.dumps(out)[:4000], ms, tin, tout, time.time()))

    def log_action(self, run_id, agent, tool, args, result, status, key):
        self._x("INSERT INTO actions (run_id,agent,tool,args,result,status,idem_key,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (run_id, agent, tool, json.dumps(args), json.dumps(result)[:4000], status, key, time.time()))

    def actions_for(self, run_id):
        return [dict(r) for r in self._x("SELECT * FROM actions WHERE run_id=%s ORDER BY id", (run_id,)).fetchall()]

    def calls_for(self, run_id):
        return [dict(r) for r in self._x("SELECT * FROM agent_calls WHERE run_id=%s ORDER BY id", (run_id,)).fetchall()]

    def agent_runs_today(self, agent):
        today_start = time.time() - (time.time() % 86400)
        return self._x(
            "SELECT COUNT(DISTINCT run_id) AS n FROM agent_calls WHERE agent=%s AND created_at >= %s",
            (agent, today_start),
        ).fetchone()["n"]

    # idempotency
    def idem_get(self, key):
        r = self._x("SELECT result FROM idem WHERE key=%s", (key,)).fetchone()
        return json.loads(r["result"]) if r else None

    def idem_put(self, key, result):
        self._x("INSERT INTO idem VALUES (%s,%s,%s) ON CONFLICT (key) DO UPDATE SET result=EXCLUDED.result, created_at=EXCLUDED.created_at",
                (key, json.dumps(result), time.time()))

    # eval history
    def save_eval_run(self, passed, total, rows):
        """rows: list of (case_id, bucket, result, detail, latency_ms)."""
        with _lock:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("INSERT INTO eval_runs (created_at, passed, total) VALUES (%s,%s,%s) RETURNING id",
                            (time.time(), passed, total))
                eval_run_id = cur.fetchone()["id"]
                for case_id, bucket, result, detail, latency_ms in rows:
                    cur.execute(
                        "INSERT INTO eval_cases (eval_run_id, case_id, bucket, result, detail, latency_ms) VALUES (%s,%s,%s,%s,%s,%s)",
                        (eval_run_id, case_id, bucket, result, detail, latency_ms))
            self.conn.commit()
            return eval_run_id

    def latest_eval(self):
        run = self._x("SELECT * FROM eval_runs ORDER BY id DESC LIMIT 1").fetchone()
        if not run: return None
        cases = self._x("SELECT * FROM eval_cases WHERE eval_run_id=%s ORDER BY id", (run["id"],)).fetchall()
        return {"run": dict(run), "cases": [dict(c) for c in cases]}
