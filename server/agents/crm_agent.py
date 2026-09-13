from agents.base import Agent
from config import SMART_MODEL

class CRMAgent(Agent):
    name = "crm"; model = SMART_MODEL
    system = """You sync a qualified lead into the CRM. You may ONLY use CRM tools.
Procedure:
1. search_crm_contact by email.
2. If null -> create_crm_contact, then create_crm_deal.
3. If found -> update_crm_contact with any new fields (name/company) that were null; if the contact has an
   open deal (open_deal_id not null) do NOT create another; else create_crm_deal.
Never create a contact you did not first search for. When done return ONLY JSON:
{"status": "ok", "contact_id": str, "deal_id": str|null, "was_duplicate": bool, "summary": str}
If create_crm_deal returns deal_skipped true, still return status ok with deal_id null and explain in summary.
If a tool errors twice, return {"status": "error", "reason": str}."""
