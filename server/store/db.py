"""SQLite state: runs, agent_calls, actions, idempotency cache."""
import sqlite3, json, time, threading
from config import DB_PATH

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY, email_id TEXT UNIQUE, state TEXT, context TEXT,
  created_at REAL, updated_at REAL);
CREATE TABLE IF NOT EXISTS agent_calls (
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, agent TEXT,
  state_in TEXT, state_out TEXT, input TEXT, output TEXT,
  latency_ms INTEGER, tokens_in INTEGER, tokens_out INTEGER, created_at REAL);
CREATE TABLE IF NOT EXISTS actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, agent TEXT, tool TEXT,
  args TEXT, result TEXT, status TEXT, idem_key TEXT, created_at REAL);
CREATE TABLE IF NOT EXISTS idem (
  key TEXT PRIMARY KEY, result TEXT, created_at REAL);
"""

class DB:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def _x(self, sql, params=()):
        with _lock:
            cur = self.conn.execute(sql, params); self.conn.commit(); return cur

    # runs
    def create_run(self, run_id, email_id, state, context):
        now = time.time()
        self._x("INSERT OR IGNORE INTO runs VALUES (?,?,?,?,?,?)",
                (run_id, email_id, state, json.dumps(context), now, now))

    def update_run(self, run_id, state, context):
        self._x("UPDATE runs SET state=?, context=?, updated_at=? WHERE id=?",
                (state, json.dumps(context), time.time(), run_id))

    def get_run(self, run_id):
        r = self._x("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        return dict(r, context=json.loads(r["context"])) if r else None

    def seen_email(self, email_id):
        return self._x("SELECT 1 FROM runs WHERE email_id=?", (email_id,)).fetchone() is not None

    # observability
    def log_agent_call(self, run_id, agent, s_in, s_out, inp, out, ms, tin, tout):
        self._x("INSERT INTO agent_calls (run_id,agent,state_in,state_out,input,output,latency_ms,tokens_in,tokens_out,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (run_id, agent, s_in, s_out, json.dumps(inp)[:4000], json.dumps(out)[:4000], ms, tin, tout, time.time()))

    def log_action(self, run_id, agent, tool, args, result, status, key):
        self._x("INSERT INTO actions (run_id,agent,tool,args,result,status,idem_key,created_at) VALUES (?,?,?,?,?,?,?,?)",
                (run_id, agent, tool, json.dumps(args), json.dumps(result)[:4000], status, key, time.time()))

    def actions_for(self, run_id):
        return [dict(r) for r in self._x("SELECT * FROM actions WHERE run_id=? ORDER BY id", (run_id,)).fetchall()]

    def calls_for(self, run_id):
        return [dict(r) for r in self._x("SELECT * FROM agent_calls WHERE run_id=? ORDER BY id", (run_id,)).fetchall()]

    # idempotency
    def idem_get(self, key):
        r = self._x("SELECT result FROM idem WHERE key=?", (key,)).fetchone()
        return json.loads(r["result"]) if r else None

    def idem_put(self, key, result):
        self._x("INSERT OR REPLACE INTO idem VALUES (?,?,?)", (key, json.dumps(result), time.time()))
