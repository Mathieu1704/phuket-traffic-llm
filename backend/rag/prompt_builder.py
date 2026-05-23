"""
Builds the RAG prompt and calls the configured LLM (Ollama, OpenAI, or Anthropic).
"""
import json
import os
import re

import ollama

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M")
OLLAMA_HOST  = os.getenv("OLLAMA_HOST",  "http://localhost:11434")
OPENAI_KEY   = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """You are an expert on Phuket traffic, tourism, and urban mobility in Thailand.
Answer ONLY using the provided context below. If the context does not contain enough information to answer confidently, say so honestly — do not invent data.
Always mention which data source(s) support your answer (e.g. "According to monthly traffic data...", "Flight statistics show...").
Be concise and precise. Answer in the same language as the question."""

REFINE_SYSTEM = """You are a writing assistant. Take the raw answer below and rewrite it to be clear and user-friendly.
CRITICAL RULES:
- Keep EVERY numeric value exactly as stated — do not drop, round, or summarize any numbers.
- Keep ALL time periods listed — do not merge or omit any.
- Do not add any information not present in the original answer.
- Do not remove cited sources.
Use bullet points or short paragraphs where appropriate."""

CHART_INSTRUCTION = """
If your answer contains numeric data that could be visualized as a bar or line chart, append AFTER your answer a single JSON block in EXACTLY this format (no extra text around it):
```chart
{"type":"bar","title":"<descriptive title>","data":[{"name":"<label>","value":<number>}],"unit":"<unit>"}
```
Otherwise do not include a chart block at all."""


# ---------------------------------------------------------------------------
# Private model callers
# ---------------------------------------------------------------------------

def _call_ollama(messages: list[dict], model: str = OLLAMA_MODEL) -> str:
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        res = client.chat(model=model, messages=messages, options={"temperature": 0})
        return res["message"]["content"]
    except Exception as e:
        return f"[LLM unavailable — Ollama error: {e}]"


def _call_openai(messages: list[dict], model: str = "gpt-4o-mini") -> str:
    if not OPENAI_KEY:
        return "[OpenAI unavailable — OPENAI_API_KEY not set]"
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_KEY)
        res = client.chat.completions.create(model=model, messages=messages)
        return res.choices[0].message.content or ""
    except Exception as e:
        return f"[OpenAI error: {e}]"


def _call_anthropic(messages: list[dict], model: str = "claude-haiku-4-5-20251001") -> str:
    if not ANTHROPIC_KEY:
        return "[Anthropic unavailable — ANTHROPIC_API_KEY not set]"
    try:
        import anthropic
        system = next((m["content"] for m in messages if m["role"] == "system"), SYSTEM_PROMPT)
        user_msgs = [m for m in messages if m["role"] != "system"]
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        res = client.messages.create(
            model=model, max_tokens=1024, system=system, messages=user_msgs,
        )
        return res.content[0].text
    except Exception as e:
        return f"[Anthropic error: {e}]"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def call_llm(prompt: str, model: str = "llama3.1:8b-instruct-q4_K_M", system: str = SYSTEM_PROMPT) -> str:
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": prompt},
    ]
    if model.startswith("gpt-"):
        return _call_openai(messages, model=model)
    if model.startswith("claude-"):
        return _call_anthropic(messages, model=model)
    # Any other model → Ollama (phi3:mini, qwen2.5:14b, llama3.1:8b, etc.)
    return _call_ollama(messages, model=model)


def refine_answer(raw: str, model: str = "ollama") -> str:
    prompt = f"Raw answer to improve:\n\n{raw}\n\nRewrite it to be more user-friendly."
    return call_llm(prompt, model=model, system=REFINE_SYSTEM)


def _extract_json_object(text: str, start: int) -> tuple[str, int] | None:
    """Extract a complete JSON object starting at `start` using brace counting."""
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == '\\' and in_str:
            escape = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return text[start:i+1], i + 1
    return None


def parse_chart_from_response(text: str) -> tuple[str, dict | None]:
    """Extract chart JSON from text — handles ```chart blocks or any JSON with type+data."""
    # 1. Try ```chart ... ``` block
    match = re.search(r"```chart\s*(\{)", text, re.DOTALL)
    if match:
        result = _extract_json_object(text, match.start(1))
        if result:
            raw_json, end = result
            try:
                return text[:match.start()].strip(), json.loads(raw_json)
            except json.JSONDecodeError:
                pass

    # 2. Find any { that starts a JSON with "type": "bar"|"line"
    for match in re.finditer(r'\{', text):
        result = _extract_json_object(text, match.start())
        if not result:
            continue
        raw_json, _ = result
        if '"type"' not in raw_json or '"data"' not in raw_json:
            continue
        try:
            chart = json.loads(raw_json)
            if chart.get("type") in ("bar", "line") and isinstance(chart.get("data"), list):
                clean = text[:match.start()].strip().rstrip("Chart:").strip()
                return clean, chart
        except json.JSONDecodeError:
            continue

    # 3. Fallback: auto-build chart from bullet list of numeric data in the text
    chart = _auto_chart_from_text(text)
    if chart:
        return text.strip(), chart

    return text.strip(), None


def _auto_chart_from_text(text: str) -> dict | None:
    """Build a bar chart from any 'label: value unit' pattern in the text."""
    # Strip markdown bold/italic and bullet markers before matching
    clean = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)  # remove **bold**
    pattern = re.compile(
        r'^[\-\*\•]?\s*([A-Za-z][^\n:]{2,50}):\s*(\d+\.?\d*)\s*(km/h|TT ratio|passengers|mm|°C)?',
        re.MULTILINE
    )
    matches = pattern.findall(clean)
    # Filter out lines that are clearly not data (too generic)
    SKIP = {'source', 'note', 'data', 'these', 'this', 'the', 'based'}
    matches = [m for m in matches if m[0].strip().lower().split()[0] not in SKIP]

    if len(matches) < 3:
        return None

    unit = next((m[2] for m in matches if m[2]), '')
    data = [{'name': m[0].strip(), 'value': float(m[1])} for m in matches]

    first_line = text.strip().split('\n')[0].strip('# *').strip()
    title = first_line[:60] if len(first_line) > 5 else 'Data'

    return {'type': 'bar', 'title': title, 'data': data, 'unit': unit}


_WHATIF_KEYWORDS = (
    "what if", "what would happen", "what would change", "suppose", "assuming",
    "if rainfall", "if rain", "if pax", "if flights", "if passengers",
    "if there were", "if we had", "if traffic", "if congestion",
    "double", "triple", "increase by", "decrease by", "reduce by",
    "hypothetical", "scenario", "counterfactual",
)

_WHATIF_INSTRUCTION = (
    "\n\nIMPORTANT: This is a counterfactual/what-if question. "
    "Reason about the hypothetical scenario described, comparing it to the historical baseline. "
    "Explain what would likely change and why, using the context above as the reference point."
)


def _is_whatif(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in _WHATIF_KEYWORDS)


def build_prompt(question: str, context_chunks: list[dict],
                 live_context: str = "", include_chart: bool = False) -> str:
    sections = []

    if live_context:
        sections.append(f"LIVE DATA (real-time, highest priority):\n{live_context}")

    if not context_chunks:
        sections.append("[No relevant historical data found in the database for this query.]")
    else:
        lines = []
        for i, chunk in enumerate(context_chunks, 1):
            src = chunk["metadata"].get("source", "unknown")
            lines.append(f"[{i}] SOURCE: {src}\n{chunk['text']}")
        sections.append("HISTORICAL DATABASE CONTEXT:\n" + "\n\n".join(lines))

    context_block = "\n\n---\n\n".join(sections)
    chart_hint = CHART_INSTRUCTION if include_chart else ""
    whatif_hint = _WHATIF_INSTRUCTION if _is_whatif(question) else ""

    return f"""Context from Phuket traffic database:

{context_block}

---
Question: {question}{whatif_hint}{chart_hint}"""
