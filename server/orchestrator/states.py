from enum import Enum

class State(str, Enum):
    RECEIVED = "RECEIVED"
    ROUTED = "ROUTED"
    EXTRACTED = "EXTRACTED"
    CRITIQUED = "CRITIQUED"
    CRM_SYNCED = "CRM_SYNCED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    SCHEDULED = "SCHEDULED"
    DONE = "DONE"
    ESCALATED = "ESCALATED"
    QUARANTINED = "QUARANTINED"
    FAILED = "FAILED"

TERMINAL = {State.DONE, State.ESCALATED, State.QUARANTINED, State.FAILED}

# state -> {event: next_state}. The orchestrator is a table, not an LLM.
TRANSITIONS = {
    State.RECEIVED:  {"lead": State.ROUTED, "not_lead": State.DONE, "ambiguous": State.ESCALATED},
    # each state = the stage that has COMPLETED; the event = outcome of the NEXT stage
    State.ROUTED:    {"ok": State.EXTRACTED, "error": State.ESCALATED},                                   # extractor
    State.EXTRACTED: {"pass": State.CRITIQUED, "low_confidence": State.ESCALATED, "injection": State.QUARANTINED},  # critic
    State.CRITIQUED: {"ok": State.CRM_SYNCED, "error": State.ESCALATED},                                  # crm agent
    State.CRM_SYNCED: {"ok": State.AWAITING_APPROVAL},                                                     # slack card posted
    State.AWAITING_APPROVAL: {"approve": State.SCHEDULED, "reject": State.DONE},
    State.SCHEDULED: {"ok": State.DONE, "error": State.ESCALATED},
}

def next_state(state: State, event: str) -> State:
    try:
        return TRANSITIONS[state][event]
    except KeyError:
        raise ValueError(f"illegal transition {state} --{event}-->")
