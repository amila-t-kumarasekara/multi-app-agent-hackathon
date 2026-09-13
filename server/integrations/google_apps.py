"""Gmail + Calendar on one OAuth client. First run opens a browser; token.json persists."""
import os, base64, datetime as dt
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tools.executor import TransientError

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly",
          "https://www.googleapis.com/auth/gmail.send",
          "https://www.googleapis.com/auth/calendar.events",
          "https://www.googleapis.com/auth/calendar.readonly"]

def creds():
    tok = os.getenv("GOOGLE_TOKEN", "token.json")
    if os.path.exists(tok): return Credentials.from_authorized_user_file(tok, SCOPES)
    c = InstalledAppFlow.from_client_secrets_file(os.getenv("GOOGLE_CREDENTIALS", "credentials.json"), SCOPES).run_local_server(port=0)
    open(tok, "w").write(c.to_json()); return c

def _wrap(fn):
    try: return fn()
    except HttpError as e:
        if e.resp.status in (429, 500, 502, 503): raise TransientError(str(e))
        raise

class GmailLive:
    def __init__(self, c=None): self.svc = build("gmail", "v1", credentials=c or creds())
    def fetch_unread(self):
        res = _wrap(lambda: self.svc.users().messages().list(userId="me", q="is:unread in:inbox", maxResults=10).execute())
        out = []
        for m in res.get("messages", []):
            full = self.svc.users().messages().get(userId="me", id=m["id"], format="full").execute()
            hdr = {h["name"].lower(): h["value"] for h in full["payload"]["headers"]}
            out.append({"id": m["id"], "thread_id": full["threadId"], "from": hdr.get("from", ""),
                        "subject": hdr.get("subject", ""), "body": _body(full["payload"])})
        return out
    def send(self, a):
        msg = MIMEText(a["body"]); msg["to"] = a["to"]; msg["subject"] = a["subject"]
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        r = _wrap(lambda: self.svc.users().messages().send(userId="me", body={"raw": raw}).execute())
        return {"id": r["id"], "sent": True}

def _body(p):
    if p.get("body", {}).get("data"): return base64.urlsafe_b64decode(p["body"]["data"]).decode(errors="ignore")
    for part in p.get("parts", []):
        if part["mimeType"] == "text/plain" and part["body"].get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode(errors="ignore")
    for part in p.get("parts", []):
        b = _body(part)
        if b: return b
    return ""

class CalendarLive:
    def __init__(self, c=None, cal_id=None):
        self.svc = build("calendar", "v3", credentials=c or creds()); self.cal = cal_id or os.getenv("CALENDAR_ID", "primary")
    def free_slots(self, preferred=None):
        now = dt.datetime.utcnow(); start = now + dt.timedelta(days=1); end = start + dt.timedelta(days=7)
        fb = _wrap(lambda: self.svc.freebusy().query(body={"timeMin": start.isoformat()+"Z", "timeMax": end.isoformat()+"Z",
                                                            "items": [{"id": self.cal}]}).execute())
        busy = [(dt.datetime.fromisoformat(b["start"].rstrip("Z")), dt.datetime.fromisoformat(b["end"].rstrip("Z")))
                for b in fb["calendars"][self.cal]["busy"]]
        slots, t = [], start.replace(hour=9, minute=0, second=0, microsecond=0)
        while t < end and len(slots) < 3:
            if t.weekday() < 5 and 9 <= t.hour < 17:
                e = t + dt.timedelta(minutes=30)
                if not any(bs < e and be > t for bs, be in busy): slots.append(t.isoformat()+"Z")
            t += dt.timedelta(minutes=30)
        return slots
    def create_event(self, a):
        s = dt.datetime.fromisoformat(a["start"].rstrip("Z")); e = s + dt.timedelta(minutes=30)
        ev = _wrap(lambda: self.svc.events().insert(calendarId=self.cal, sendUpdates="all", body={
            "summary": a["title"], "start": {"dateTime": s.isoformat()+"Z"}, "end": {"dateTime": e.isoformat()+"Z"},
            "attendees": [{"email": a["attendee_email"]}]}).execute())
        return {"id": ev["id"], "start": a["start"], "link": ev.get("htmlLink")}
