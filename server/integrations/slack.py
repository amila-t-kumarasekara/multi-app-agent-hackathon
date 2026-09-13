import os, requests
from tools.executor import TransientError

class SlackLive:
    def __init__(self, token=None, channel=None):
        self.h = {"Authorization": f"Bearer {token or os.environ['SLACK_BOT_TOKEN']}"}
        self.channel = channel or os.environ["SLACK_CHANNEL"]
    def _post(self, payload):
        r = requests.post("https://slack.com/api/chat.postMessage", headers=self.h, json=payload, timeout=5)
        if r.status_code in (429, 500, 502, 503): raise TransientError(f"slack {r.status_code}")
        j = r.json()
        if not j.get("ok"): raise RuntimeError(f"slack error {j.get('error')}")
        return {"ts": j["ts"]}
    def post_message(self, a):
        return self._post({"channel": self.channel, "text": a["text"]})
    def post_approval(self, a):
        lead, crm, rid = a["lead"], a["crm"], a["run_id"]
        text = (f"*New lead* — {lead.get('name') or '?'} ({lead.get('email')}) at {lead.get('company') or '?'}\n"
                f"*Intent:* {lead.get('intent')}\n*Urgency:* {lead.get('urgency')}  ·  *Confidence:* {a.get('confidence')}\n"
                f"*CRM:* {'updated existing' if crm.get('was_duplicate') else 'created'} contact {crm.get('contact_id')}")
        return self._post({"channel": self.channel, "text": text, "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
            {"type": "actions", "elements": [
                {"type": "button", "style": "primary", "text": {"type": "plain_text", "text": "Approve & book"},
                 "action_id": "approve_lead", "value": rid},
                {"type": "button", "style": "danger", "text": {"type": "plain_text", "text": "Reject"},
                 "action_id": "reject_lead", "value": rid}]}]})
