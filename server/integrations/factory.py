import json
import os
from config import USE_FAKES, CRM_PROVIDER
from integrations.base import Apps

def _oauth_client_secrets_path():
    return os.getenv("GOOGLE_CREDENTIALS", "credentials.json")

def _oauth_token_path():
    return os.getenv("GOOGLE_TOKEN", "token.json")

def _valid_oauth_client_secrets(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False
    if data.get("type") == "service_account":
        return False
    return "installed" in data or "web" in data

def _google_mode():
    """live | invalid_cred | missing"""
    if os.path.exists(_oauth_token_path()):
        return "live"
    cred = _oauth_client_secrets_path()
    if not os.path.exists(cred):
        return "missing"
    if _valid_oauth_client_secrets(cred):
        return "live"
    return "invalid_cred"

def build_apps():
    if USE_FAKES:
        from integrations.fakes import FakeCRM, FakeGmail, FakeSlack, FakeCalendar
        return Apps(FakeCRM(), FakeGmail(), FakeSlack(), FakeCalendar())
    from integrations.crm import HubSpotCRM, AirtableCRM
    from integrations.slack import SlackLive
    from integrations.fakes import FakeGmail, FakeCalendar
    crm = HubSpotCRM() if CRM_PROVIDER == "hubspot" else AirtableCRM()
    slack = SlackLive()
    gmode = _google_mode()
    if gmode == "live":
        from integrations.google_apps import GmailLive, CalendarLive, creds
        try:
            c = creds()
            gmail, cal = GmailLive(c), CalendarLive(c)
        except ValueError as e:
            print(f"Google OAuth setup failed ({e}); using fake Gmail/Calendar.")
            gmail, cal = FakeGmail(), FakeCalendar()
    elif gmode == "invalid_cred":
        print(
            "credentials.json is not an OAuth Desktop/Web client file "
            "(service accounts are not supported here). Using fake Gmail/Calendar. "
            "In Google Cloud: APIs & Services → Credentials → Create OAuth client → Desktop app, "
            "download JSON as server/credentials.json, then restart and complete the browser flow."
        )
        gmail, cal = FakeGmail(), FakeCalendar()
    else:
        print(
            "Google credentials not found; using fake Gmail/Calendar. "
            "Add credentials.json (or token.json) under server/ for live Google."
        )
        gmail, cal = FakeGmail(), FakeCalendar()
    return Apps(crm, gmail, slack, cal)
