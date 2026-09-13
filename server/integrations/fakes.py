"""In-memory fakes. Support fault injection for evals and the demo."""
import itertools, datetime as dt
from tools.executor import TransientError

class FakeCRM:
    def __init__(self, contacts=None, fail_mode=None):
        self.contacts = {c["email"].lower(): c for c in (contacts or [])}
        self.deals, self.fail_mode, self._n = [], fail_mode, itertools.count(1)
        self.calls = []
    def _maybe_fail(self):
        if self.fail_mode == "500": raise TransientError("CRM 500")
        if self.fail_mode == "429": raise TransientError("CRM 429 rate limited")
        if self.fail_mode == "hard": raise RuntimeError("CRM 400 bad request")
    def search(self, email):
        self.calls.append("search"); self._maybe_fail()
        return self.contacts.get(email.lower())
    def create(self, a):
        self.calls.append("create"); self._maybe_fail()
        c = {"id": f"c{next(self._n)}", "email": a["email"], "name": a.get("name"),
             "company": a.get("company"), "open_deal_id": None}
        self.contacts[a["email"].lower()] = c; return c
    def update(self, contact_id, fields):
        self.calls.append("update"); self._maybe_fail()
        for c in self.contacts.values():
            if c["id"] == contact_id: c.update({k: v for k, v in fields.items() if v}); return c
        raise RuntimeError("contact not found")
    def create_deal(self, a):
        self.calls.append("create_deal"); self._maybe_fail()
        d = {"id": f"d{next(self._n)}", "contact_id": a["contact_id"], "title": a["title"]}
        self.deals.append(d)
        for c in self.contacts.values():
            if c["id"] == a["contact_id"]: c["open_deal_id"] = d["id"]
        return d

class FakeGmail:
    def __init__(self, inbox=None, fail_send=False):
        self.inbox, self.sent, self.fail_send = list(inbox or []), [], fail_send
    def fetch_unread(self): return self.inbox
    def send(self, a):
        if self.fail_send: raise TransientError("gmail send 503")
        self.sent.append(a); return {"id": f"m{len(self.sent)}", "sent": True}

class FakeSlack:
    def __init__(self, timeout=False):
        self.posts, self.timeout = [], timeout
    def post_approval(self, a):
        if self.timeout: raise TransientError("slack timeout")
        self.posts.append(("approval", a)); return {"ts": str(len(self.posts))}
    def post_message(self, a):
        self.posts.append(("message", a)); return {"ts": str(len(self.posts))}

class FakeCalendar:
    def __init__(self, all_busy=False):
        self.events, self.all_busy = [], all_busy
    def free_slots(self, preferred=None):
        if self.all_busy: return []
        base = dt.datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + dt.timedelta(days=1)
        return [(base + dt.timedelta(days=i)).isoformat() for i in range(3)]
    def create_event(self, a):
        if self.all_busy: raise RuntimeError("no availability")
        self.events.append(a); return {"id": f"e{len(self.events)}", "start": a["start"]}
