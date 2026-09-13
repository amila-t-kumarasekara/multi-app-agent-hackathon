"""Live CRM. HubSpot via private-app token, or Airtable as a 10-minute fallback."""
import os, requests
from tools.executor import TransientError

def _check(r):
    if r.status_code in (429, 500, 502, 503, 504): raise TransientError(f"{r.status_code} {r.text[:200]}")
    r.raise_for_status(); return r.json()

class HubSpotCRM:
    BASE = "https://api.hubapi.com/crm/v3/objects"
    def __init__(self, token=None):
        self.h = {"Authorization": f"Bearer {token or os.environ['HUBSPOT_TOKEN']}"}
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
        j = _check(requests.post(f"{self.BASE}/deals", headers=self.h, json={
            "properties": {"dealname": a["title"], "dealstage": "appointmentscheduled", "pipeline": "default"},
            "associations": [{"to": {"id": a["contact_id"]}, "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}]}]}, timeout=10))
        return {"id": j["id"], "contact_id": a["contact_id"], "title": a["title"]}

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
