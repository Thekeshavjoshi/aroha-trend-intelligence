import json
import re
from src.llm.client import generate_response


def _parse_json(response):
    if not response:
        return None
    cleaned = re.sub(r"```(?:json)?\s*|```", "", response.strip(), flags=re.I).strip()
    for candidate in (response.strip(), cleaned):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                for key in ("creative_directions", "directions", "results"):
                    if isinstance(parsed.get(key), list):
                        return parsed[key]
        except json.JSONDecodeError:
            pass
    a, b = cleaned.find("["), cleaned.rfind("]")
    if a >= 0 and b > a:
        try:
            parsed = json.loads(cleaned[a:b+1])
            return parsed if isinstance(parsed, list) else None
        except json.JSONDecodeError:
            pass
    return None


def generate_creative_directions(opportunities: list[dict]) -> list[dict]:
    selected = opportunities[:1]
    payload = json.dumps(selected, indent=2, ensure_ascii=False)
    prompt = f"""
You are AROHA's senior creative strategist.

The user selected ONE opportunity space. Create THREE genuinely distinct creative territories that act on THIS opportunity without changing its core evidence.

Rules:
- Anchor every direction to the supplied opportunity, unmet need and supporting trend.
- Do not invent statistics, brands, market claims, or unsupported facts.
- Keep the opportunity as the problem/gap; do not silently replace it with a random product idea.
- Make the three directions materially different in concept and visual territory.
- Keep every field concise: normally one sentence or a short phrase.
- Return ONLY valid JSON.

SELECTED OPPORTUNITY:
{payload}

Return exactly:
[
  {{"name":"","concept":"","creative_direction":"","target_audience":"","rationale":"","supporting_trend":"","supporting_evidence":[]}}
]
"""
    parsed = _parse_json(generate_response(prompt)) or []
    return [x for x in parsed if isinstance(x, dict) and not x.get("error")][:3]
