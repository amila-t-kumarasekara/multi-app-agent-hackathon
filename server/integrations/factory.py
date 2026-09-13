from config import USE_FAKES, CRM_PROVIDER
from integrations.base import Apps

def build_apps():
    if USE_FAKES:
        from integrations.fakes import FakeCRM, FakeGmail, FakeSlack, FakeCalendar
        return Apps(FakeCRM(), FakeGmail(), FakeSlack(), FakeCalendar())
    from integrations.crm import HubSpotCRM, AirtableCRM
    from integrations.slack import SlackLive
    from integrations.google_apps import GmailLive, CalendarLive, creds
    c = creds()
    crm = HubSpotCRM() if CRM_PROVIDER == "hubspot" else AirtableCRM()
    return Apps(crm, GmailLive(c), SlackLive(), CalendarLive(c))
