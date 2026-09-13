"""Email IDs from eval fixtures — excluded from the live dashboard feed."""
import glob
import json
import os

_CASE_DIR = os.path.join(os.path.dirname(__file__), "cases")


def eval_email_ids():
    ids = set()
    for path in glob.glob(os.path.join(_CASE_DIR, "*.json")):
        with open(path, encoding="utf-8") as f:
            case = json.load(f)
        ids.add(case["email"]["id"])
    return ids


def is_live_run(run: dict) -> bool:
    ctx = run.get("context") or {}
    if ctx.get("source") == "eval":
        return False
    if run.get("email_id") in eval_email_ids():
        return False
    return True
