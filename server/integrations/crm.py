"""Live CRM. HubSpot via private-app token, or Airtable as a 10-minute fallback."""
import os, requests
from tools.executor import TransientError

def _check(r, *, hint=""):
    if r.status_code in (429, 500, 502, 503, 504):
        raise TransientError(f"{r.status_code} {r.text[:200]}")
    if r.status_code == 403:
        extra = hint or r.text[:240]
        raise RuntimeError(
            f"HubSpot 403 Forbidden — private app token lacks permission. {extra}"
        )
    r.raise_for_status()
    return r.json()

HUBSPOT_DEAL_SCOPES = ("crm.objects.deals.read", "crm.objects.deals.write")


def hubspot_token_scopes(token):
    """OAuth access-token introspection; returns None for private app tokens (pat-…)."""
    if not token or token.startswith("pat-"):
        return None
    r = requests.get(f"https://api.hubapi.com/oauth/v1/access-tokens/{token}", timeout=10)
    if not r.ok:
        return None
    return r.json().get("scopes") or []


class HubSpotCRM:
    BASE = "https://api.hubapi.com/crm/v3/objects"
    PIPELINES = "https://api.hubapi.com/crm/v3/pipelines/deals"
    ASSOC_V4 = "https://api.hubapi.com/crm/v4/objects/deals"

    def __init__(self, token=None):
        self.token = token or os.environ["HUBSPOT_TOKEN"]
        self.h = {"Authorization": f"Bearer {self.token}"}
        self._deal_defaults = None

    def _scope_hint(self):
        scopes = hubspot_token_scopes(self.token)
        if scopes is not None:
            missing = [s for s in HUBSPOT_DEAL_SCOPES if s not in scopes]
            if missing:
                return (
                    f"Token is missing scopes: {', '.join(missing)}. "
                    "In HubSpot: Private app → Scopes → save → Regenerate token → update HUBSPOT_TOKEN → restart uvicorn."
                )
            return (
                f"Token has deals scopes but HubSpot still returned 403 "
                f"(check Sales/Deals enabled on portal). Scopes: {', '.join(scopes[:12])}…"
            )
        return (
            "HubSpot returned 403 on deals — enable crm.objects.deals.read/write on the private app, "
            "regenerate the token, update HUBSPOT_TOKEN, and restart uvicorn."
        )

    def _deal_pipeline_and_stage(self):
        if self._deal_defaults:
            return self._deal_defaults
        j = _check(
            requests.get(self.PIPELINES, headers=self.h, timeout=10),
            hint="Add scopes: crm.objects.deals.read and crm.objects.deals.write on the HubSpot private app.",
        )
        pipelines = j.get("results") or []
        if not pipelines:
            self._deal_defaults = ("default", "appointmentscheduled")
            return self._deal_defaults
        pipe = pipelines[0]
        stages = pipe.get("stages") or []
        stage_id = stages[0]["id"] if stages else "appointmentscheduled"
        self._deal_defaults = (str(pipe["id"]), stage_id)
        return self._deal_defaults
    def search(self, email):
        j = _check(requests.post(f"{self.BASE}/contacts/search", headers=self.h, json={
            "filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}],
            "properties": ["email", "firstname", "lastname", "company"]}, timeout=10))
        if not j.get("results"): return None
        c = j["results"][0]; p = c["properties"]
        deals = _check(requests.get(f"{self.BASE}/contacts/{c['id']}/associations/deals", headers=self.h, timeout=10))
        open_deal = deals["results"][0]["id"] if deals.get("results") else None
        return {"id": c["id"], "email": p.get("email"), "name": f"{p.get('firstname','')} {p.get('lastname','')}".strip() or None,
                "company": p.get("company"), "open_deal_id": open_deal}
    def create(self, a):
        first, _, last = (a.get("name") or "").partition(" ")
        j = _check(requests.post(f"{self.BASE}/contacts", headers=self.h, json={"properties": {
            "email": a["email"], "firstname": first, "lastname": last, "company": a.get("company") or ""}}, timeout=10))
        return {"id": j["id"], "email": a["email"], "name": a.get("name"), "company": a.get("company"), "open_deal_id": None}
    def update(self, contact_id, fields):
        props = {}
        if fields.get("company"): props["company"] = fields["company"]
        if fields.get("name"):
            f, _, l = fields["name"].partition(" "); props.update(firstname=f, lastname=l)
        j = _check(requests.patch(f"{self.BASE}/contacts/{contact_id}", headers=self.h, json={"properties": props}, timeout=10))
        return {"id": j["id"], **fields}
    def create_deal(self, a):
        pipeline_id, stage_id = self._deal_pipeline_and_stage()
        r = requests.post(
            f"{self.BASE}/deals",
            headers=self.h,
            json={
                "properties": {
                    "dealname": a["title"],
                    "dealstage": stage_id,
                    "pipeline": pipeline_id,
                },
            },
            timeout=10,
        )
        if r.status_code == 403:
            return {
                "id": None,
                "contact_id": a["contact_id"],
                "title": a["title"],
                "deal_skipped": True,
                "reason": self._scope_hint(),
            }
        j = _check(
            r,
            hint="Enable crm.objects.deals.read/write on the HubSpot private app and regenerate the token.",
        )
        deal_id = j["id"]
        requests.put(
            f"{self.ASSOC_V4}/{deal_id}/associations/contacts/{a['contact_id']}/3",
            headers=self.h,
            timeout=10,
        )
        return {"id": deal_id, "contact_id": a["contact_id"], "title": a["title"]}

class AirtableCRM:
    def __init__(self, token=None, base=None):
        self.h = {"Authorization": f"Bearer {token or os.environ['AIRTABLE_TOKEN']}"}
        self.url = f"https://api.airtable.com/v0/{base or os.environ['AIRTABLE_BASE']}"
    def search(self, email):
        j = _check(requests.get(f"{self.url}/Contacts", headers=self.h,
            params={"filterByFormula": f"LOWER({{Email}})='{email.lower()}'"}, timeout=10))
        if not j["records"]: return None
        r = j["records"][0]; f = r["fields"]
        return {"id": r["id"], "email": f.get("Email"), "name": f.get("Name"), "company": f.get("Company"),
                "open_deal_id": (f.get("Deals") or [None])[0]}
    def create(self, a):
        j = _check(requests.post(f"{self.url}/Contacts", headers=self.h, json={"fields": {
            "Email": a["email"], "Name": a.get("name"), "Company": a.get("company")}}, timeout=10))
        return {"id": j["id"], **a, "open_deal_id": None}
    def update(self, contact_id, fields):
        m = {"name": "Name", "company": "Company"}
        j = _check(requests.patch(f"{self.url}/Contacts/{contact_id}", headers=self.h,
            json={"fields": {m[k]: v for k, v in fields.items() if k in m and v}}, timeout=10))
        return {"id": j["id"], **fields}
    def create_deal(self, a):
        j = _check(requests.post(f"{self.url}/Deals", headers=self.h, json={"fields": {
            "Title": a["title"], "Contact": [a["contact_id"]], "Stage": "New"}}, timeout=10))
        return {"id": j["id"], "contact_id": a["contact_id"], "title": a["title"]}
