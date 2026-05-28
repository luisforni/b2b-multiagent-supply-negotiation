import json
import re
import uuid
from datetime import date, timedelta


def extract_json(text: str) -> dict:
    """Parse the first JSON object found in an LLM response."""
    try:
        return json.loads(text.strip())
    except (json.JSONDecodeError, AttributeError):
        pass

    # JSON inside a fenced code block
    match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Bare JSON object (greedy innermost not reliable — use last occurrence)
    matches = list(re.finditer(r"\{[\s\S]*?\}", text))
    for m in reversed(matches):
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            continue

    return {}


def new_offer_id() -> str:
    return str(uuid.uuid4())[:6].upper()


def delivery_date_str(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def contract_id() -> str:
    today = date.today().strftime("%Y%m%d")
    suffix = str(uuid.uuid4())[:4].upper()
    return f"CTR-{today}-{suffix}"
