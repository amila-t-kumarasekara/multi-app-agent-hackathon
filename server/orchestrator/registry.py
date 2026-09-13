"""Least-privilege tool registry. Enforced in the executor, not in prompts."""
REGISTRY = {
    "router":    set(),
    "extractor": set(),
    "critic":    set(),
    "crm":       {"search_crm_contact", "create_crm_contact", "update_crm_contact", "create_crm_deal"},
    "scheduler": {"get_calendar_availability", "create_calendar_event", "send_email_reply"},
    "orchestrator": {"post_slack_approval", "post_slack_message"},
}
WRITE_TOOLS = {"create_crm_contact", "update_crm_contact", "create_crm_deal",
               "create_calendar_event", "send_email_reply", "post_slack_approval", "post_slack_message"}
