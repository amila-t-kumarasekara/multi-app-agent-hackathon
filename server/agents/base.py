"""Agent base: bounded tool-calling loop, scoped tools, structured JSON output."""
import json, time, re
import anthropic
from tools.schemas import schemas_for
from orchestrator.registry import REGISTRY
from config import MAX_STEPS

_client = None
def client():
    global _client
    if _client is None: _client = anthropic.Anthropic()
    return _client

def parse_json(text):
    text = re.sub(r"```(?:json)?|```", "", text).strip()
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)

class Agent:
    name: str = "base"
    model: str = ""
    system: str = ""
    json_output: bool = True

    def __init__(self, executor, db, model=None):
        self.executor, self.db = executor, db
        if model: self.model = model
        self.tools = schemas_for(sorted(REGISTRY[self.name]))

    def run(self, run_id, state_in, user_content: str):
        t0 = time.time(); tin = tout = 0
        messages = [{"role": "user", "content": user_content}]
        final_text = ""
        for _ in range(MAX_STEPS):
            kw = dict(model=self.model, max_tokens=1500, system=self.system, messages=messages)
            if self.tools: kw["tools"] = self.tools
            resp = client().messages.create(**kw)
            tin += resp.usage.input_tokens; tout += resp.usage.output_tokens
            messages.append({"role": "assistant", "content": resp.content})
            final_text = "".join(b.text for b in resp.content if b.type == "text")
            if resp.stop_reason != "tool_use":
                break
            results = []
            for b in resp.content:
                if b.type != "tool_use": continue
                try:
                    out = self.executor.execute(self.name, b.name, b.input, run_id)
                    results.append({"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(out)})
                except Exception as e:
                    results.append({"type": "tool_result", "tool_use_id": b.id, "content": json.dumps({"error": str(e)}), "is_error": True})
            messages.append({"role": "user", "content": results})
        else:
            final_text = json.dumps({"status": "error", "reason": "max_steps_exceeded"})

        out = parse_json(final_text) if self.json_output else {"text": final_text}
        self.db.log_agent_call(run_id, self.name, state_in, out.get("status") or out.get("verdict") or "",
                               user_content, out, int((time.time()-t0)*1000), tin, tout)
        return out
