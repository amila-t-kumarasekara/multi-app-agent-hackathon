from agents.base import Agent
from config import SMART_MODEL

class Scheduler(Agent):
    name = "scheduler"; model = SMART_MODEL
    system = """A human has APPROVED this lead. Book one 30-minute intro call and confirm by email.
Procedure: get_calendar_availability (pass timing_preference) -> create_calendar_event at the first slot
-> send_email_reply with a short, warm confirmation including the time. Exactly one event, one email.
Return ONLY JSON: {"status": "ok", "event_start": str, "summary": str} or {"status": "error", "reason": str}."""
