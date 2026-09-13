"""Live integration status for the dashboard (account labels, connection probes)."""
import os
import requests
from config import USE_FAKES, CRM_PROVIDER
from integrations.fakes import FakeCRM, FakeGmail, FakeCalendar, FakeSlack
from integrations.crm import HubSpotCRM, AirtableCRM, hubspot_token_scopes, HUBSPOT_DEAL_SCOPES
from integrations.factory import _google_mode


def _item(name, icon, account, connected, detail=""):
    return {
        "name": name,
        "icon": icon,
        "account": account,
        "detail": detail,
        "status": "Connected" if connected else "Disconnected",
        "statusClass": "tag-accent-2" if connected else "tag-neutral",
        "actionLabel": "Manage" if connected else "Connect",
    }


def _google_disconnect_reason():
    if USE_FAKES:
        return "USE_FAKES=1 — in-memory demo Gmail"
    mode = _google_mode()
    if mode == "invalid_cred":
        return "credentials.json must be OAuth Desktop app JSON (not a service account)"
    if mode == "missing":
        return "Add credentials.json or complete OAuth (token.json)"
    return "Google OAuth not active for this process"


def _slack_channel_label(token, channel_id):
    if not channel_id:
        return "channel not set"
    try:
        r = requests.get(
            "https://slack.com/api/conversations.info",
            headers={"Authorization": f"Bearer {token}"},
            params={"channel": channel_id},
            timeout=5,
        ).json()
        if r.get("ok"):
            ch = r["channel"]
            name = ch.get("name", channel_id)
            return f"#{name}" if ch.get("is_channel") else name
    except requests.RequestException:
        pass
    return channel_id


def _slack_status(slack):
    if isinstance(slack, FakeSlack):
        return _item("Slack", "message", "Demo (in-memory)", False, "USE_FAKES=1")
    token = os.getenv("SLACK_BOT_TOKEN", "").strip()
    channel_id = (os.getenv("SLACK_CHANNEL_ID") or os.getenv("SLACK_CHANNEL") or "").strip()
    if not token:
        return _item("Slack", "message", "Not configured", False, "Set SLACK_BOT_TOKEN in .env")
    try:
        r = requests.post(
            "https://slack.com/api/auth.test",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        ).json()
    except requests.RequestException as e:
        return _item("Slack", "message", "Unreachable", False, str(e))
    if not r.get("ok"):
        return _item("Slack", "message", "Auth failed", False, r.get("error", "unknown"))
    team = r.get("team", "workspace")
    bot_user = r.get("user", "bot")
    bot_id = r.get("user_id", "")
    ch_label = _slack_channel_label(token, channel_id) if channel_id else "(SLACK_CHANNEL_ID not set)"
    account = f"{team} · {ch_label}"
    detail = f"Workspace: {team} · Bot: @{bot_user} (ID {bot_id}) · Channel: {ch_label}"
    if not channel_id:
        return _item("Slack", "message", account, False, detail)
    return _item("Slack", "message", account, True, detail)


def _crm_status(crm):
    label = f"CRM ({CRM_PROVIDER.title()})"
    if isinstance(crm, FakeCRM):
        return _item(label, "database", "Demo (in-memory)", False, "USE_FAKES=1")
    if isinstance(crm, HubSpotCRM):
        token = os.getenv("HUBSPOT_TOKEN", "").strip()
        if not token:
            return _item(label, "database", "Not configured", False, "Set HUBSPOT_TOKEN in .env")
        try:
            r = requests.get(
                "https://api.hubapi.com/account-info/v3/details",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
        except requests.RequestException as e:
            return _item(label, "database", "Unreachable", False, str(e))
        if not r.ok:
            return _item(label, "database", "Auth failed", False, f"HTTP {r.status_code}: {r.text[:120]}")
        j = r.json()
        portal = j.get("portalId", "?")
        company = j.get("companyName") or j.get("accountType") or "HubSpot"
        account = f"{company} · portal {portal}"
        scopes = hubspot_token_scopes(token) or []
        missing_deals = [s for s in HUBSPOT_DEAL_SCOPES if s not in scopes]
        pipe_r = requests.get(HubSpotCRM.PIPELINES, headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if missing_deals:
            detail = (
                f"Portal {portal} · token missing scopes: {', '.join(missing_deals)}. "
                "Private app → add scopes → Save → Regenerate token → paste new HUBSPOT_TOKEN → restart uvicorn."
            )
            return _item(label, "database", account, False, detail)
        if not pipe_r.ok:
            detail = (
                f"Portal {portal} · deals pipelines HTTP {pipe_r.status_code} — "
                f"regenerate token after scopes. {pipe_r.text[:100]}"
            )
            return _item(label, "database", account, False, detail)
        detail = f"Portal {portal} · scopes include deals · {len(pipe_r.json().get('results') or [])} pipeline(s) · tz {j.get('timeZone', '—')}"
        return _item(label, "database", account, True, detail)
    if isinstance(crm, AirtableCRM):
        base = os.getenv("AIRTABLE_BASE", "")
        token = os.getenv("AIRTABLE_TOKEN", "").strip()
        if not token or not base:
            return _item(label, "database", "Not configured", False, "Set AIRTABLE_TOKEN and AIRTABLE_BASE")
        account = f"Base {base[:8]}…" if len(base) > 8 else f"Base {base}"
        return _item(label, "database", account, True, f"Airtable base ID {base}")
    return _item(label, "database", "Unknown CRM driver", False)


def _gmail_status(gmail):
    if isinstance(gmail, FakeGmail):
        return _item("Email (Gmail)", "mail", "Not connected", False, _google_disconnect_reason())
    try:
        prof = gmail.svc.users().getProfile(userId="me").execute()
        email = prof.get("emailAddress", "unknown")
        msgs = prof.get("messagesTotal", "—")
        threads = prof.get("threadsTotal", "—")
        detail = f"Signed in as {email} · {msgs} messages · {threads} threads"
        return _item("Email (Gmail)", "mail", email, True, detail)
    except Exception as e:
        return _item("Email (Gmail)", "mail", "Error loading profile", False, str(e))


def _calendar_status(calendar):
    if isinstance(calendar, FakeCalendar):
        return _item("Google Calendar", "calendar", "Not connected", False, _google_disconnect_reason())
    try:
        meta = calendar.svc.calendars().get(calendarId=calendar.cal).execute()
        summary = meta.get("summary", calendar.cal)
        tz = meta.get("timeZone", "")
        account = summary if summary else calendar.cal
        detail = f"Calendar ID: {calendar.cal}" + (f" · {tz}" if tz else "")
        return _item("Google Calendar", "calendar", account, True, detail)
    except Exception as e:
        return _item(
            "Google Calendar",
            "calendar",
            calendar.cal,
            True,
            f"Primary calendar ({calendar.cal}) — {e}",
        )


def build_integration_list(apps):
    return [
        _gmail_status(apps.gmail),
        _crm_status(apps.crm),
        _slack_status(apps.slack),
        _calendar_status(apps.calendar),
    ]
