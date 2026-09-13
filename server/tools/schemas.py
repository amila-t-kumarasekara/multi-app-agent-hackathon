"""Tool schemas exposed to tool-using agents (Anthropic tool format)."""
TOOLS = {
    "search_crm_contact": {
        "name": "search_crm_contact",
        "description": "Find an existing CRM contact by email. Returns contact or null.",
        "input_schema": {"type": "object", "properties": {"email": {"type": "string"}}, "required": ["email"]},
    },
    "create_crm_contact": {
        "name": "create_crm_contact",
        "description": "Create a new CRM contact. Only call if search returned null.",
        "input_schema": {"type": "object", "properties": {
            "email": {"type": "string"}, "name": {"type": "string"}, "company": {"type": "string"}},
            "required": ["email", "name"]},
    },
    "update_crm_contact": {
        "name": "update_crm_contact",
        "description": "Update fields on an existing contact.",
        "input_schema": {"type": "object", "properties": {
            "contact_id": {"type": "string"}, "fields": {"type": "object"}}, "required": ["contact_id", "fields"]},
    },
    "create_crm_deal": {
        "name": "create_crm_deal",
        "description": "Create a deal attached to a contact. Skip if contact already has an open deal.",
        "input_schema": {"type": "object", "properties": {
            "contact_id": {"type": "string"}, "title": {"type": "string"}, "intent": {"type": "string"}},
            "required": ["contact_id", "title"]},
    },
    "get_calendar_availability": {
        "name": "get_calendar_availability",
        "description": "Return up to 3 free 30-minute slots (ISO datetimes) in the next 5 business days.",
        "input_schema": {"type": "object", "properties": {"preferred": {"type": "string", "description": "free-text timing preference"}}},
    },
    "create_calendar_event": {
        "name": "create_calendar_event",
        "description": "Book a 30-minute intro call at the given slot with the lead as attendee.",
        "input_schema": {"type": "object", "properties": {
            "start": {"type": "string"}, "attendee_email": {"type": "string"}, "title": {"type": "string"}},
            "required": ["start", "attendee_email", "title"]},
    },
    "send_email_reply": {
        "name": "send_email_reply",
        "description": "Reply to the lead's original email thread.",
        "input_schema": {"type": "object", "properties": {
            "to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}},
            "required": ["to", "subject", "body"]},
    },
}

def schemas_for(names):
    return [TOOLS[n] for n in names]
