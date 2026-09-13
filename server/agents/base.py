"""Agent base: bounded tool-calling loop, scoped tools, structured JSON output."""
import json, os, re, time
from google import genai
from google.genai import types
from tools.schemas import schemas_for
from orchestrator.registry import REGISTRY
from config import MAX_STEPS

_client = None

def client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client

def parse_json(text):
    text = re.sub(r"```(?:json)?|```", "", text).strip()
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)

_JSON_TYPE_TO_GEMINI = {
    "object": "OBJECT",
    "string": "STRING",
    "integer": "INTEGER",
    "number": "NUMBER",
    "boolean": "BOOLEAN",
    "array": "ARRAY",
}

def _to_gemini_schema(schema):
    if not isinstance(schema, dict):
        return schema
    out = {}
    for key, val in schema.items():
        if key == "type" and isinstance(val, str):
            out[key] = _JSON_TYPE_TO_GEMINI.get(val.lower(), val.upper())
        elif key == "properties" and isinstance(val, dict):
            out[key] = {k: _to_gemini_schema(v) for k, v in val.items()}
        elif key == "items":
            out[key] = _to_gemini_schema(val)
        else:
            out[key] = val
    return out

def _gemini_tools(anthropic_tools):
    if not anthropic_tools:
        return None
    decls = [
        types.FunctionDeclaration(
            name=t["name"],
            description=t["description"],
            parameters=_to_gemini_schema(t["input_schema"]),
        )
        for t in anthropic_tools
    ]
    return [types.Tool(function_declarations=decls)]

def _function_call_args(args):
    if args is None:
        return {}
    if isinstance(args, dict):
        return args
    if hasattr(args, "items"):
        return dict(args)
    return json.loads(args) if isinstance(args, str) else dict(args)

class Agent:
    name: str = "base"
    model: str = ""
    system: str = ""
    json_output: bool = True

    def __init__(self, executor, db, model=None):
        self.executor, self.db = executor, db
        if model:
            self.model = model
        self.tools = schemas_for(sorted(REGISTRY[self.name]))
        self._gemini_tools = _gemini_tools(self.tools)

    def run(self, run_id, state_in, user_content: str):
        t0 = time.time()
        tin = tout = 0
        contents = [
            types.Content(role="user", parts=[types.Part(text=user_content)]),
        ]
        final_text = ""
        for _ in range(MAX_STEPS):
            config_kw = dict(system_instruction=self.system, max_output_tokens=1500)
            if self._gemini_tools:
                config_kw["tools"] = self._gemini_tools
            resp = client().models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(**config_kw),
            )
            um = resp.usage_metadata
            if um:
                tin += um.prompt_token_count or 0
                tout += um.candidates_token_count or 0
            if not resp.candidates:
                break
            model_content = resp.candidates[0].content
            contents.append(model_content)
            final_text = "".join(p.text or "" for p in model_content.parts if p.text)
            fc_parts = [p for p in model_content.parts if p.function_call]
            if not fc_parts:
                break
            response_parts = []
            for part in fc_parts:
                fc = part.function_call
                name = fc.name
                try:
                    out = self.executor.execute(
                        self.name, name, _function_call_args(fc.args), run_id
                    )
                    response_parts.append(
                        types.Part.from_function_response(name=name, response={"result": out})
                    )
                except Exception as e:
                    response_parts.append(
                        types.Part.from_function_response(name=name, response={"error": str(e)})
                    )
            contents.append(types.Content(role="user", parts=response_parts))
        else:
            final_text = json.dumps({"status": "error", "reason": "max_steps_exceeded"})

        out = parse_json(final_text) if self.json_output else {"text": final_text}
        self.db.log_agent_call(
            run_id,
            self.name,
            state_in,
            out.get("status") or out.get("verdict") or "",
            user_content,
            out,
            int((time.time() - t0) * 1000),
            tin,
            tout,
        )
        return out
