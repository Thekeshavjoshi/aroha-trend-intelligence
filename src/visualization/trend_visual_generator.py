import json
import re
from src.llm.client import generate_response


def _parse(response):
    if not response:
        return []
    cleaned = re.sub(r"```(?:json)?\s*|```", "", response.strip(), flags=re.I).strip()
    for text in (response.strip(), cleaned):
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and isinstance(data.get("visuals"), list):
                return data["visuals"]
        except json.JSONDecodeError:
            pass
    a, b = cleaned.find("["), cleaned.rfind("]")
    if a >= 0 and b > a:
        try:
            data = json.loads(cleaned[a:b+1])
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            pass
    return []


def generate_trend_visual_prompts(trends: list[dict]) -> list[dict]:
    payload = json.dumps(trends[:5], indent=2, ensure_ascii=False)
    prompt = f"""
You are AROHA's visual trend editor.
Create ONE highly specific, realistic editorial visual concept for each emerging trend below.
These are AI visualizations, NOT evidence. The image should make the underlying behavior,
aesthetic or adoption pattern obvious at a glance rather than simply illustrating the trend words.
Rules:
- Depict the supplied trend directly through a concrete human behavior, product interaction, setting, material, styling choice or observable pattern.
- Do not invent statistics, brands, logos, watermarks or readable text.
- Avoid generic futuristic AI imagery, floating interfaces and abstract technology clichés.
- Prefer realistic editorial, product or lifestyle photography with a strong point of view.
- Make each prompt specific and visually distinct.
- Keep each prompt under 120 words.
- Return ONLY valid JSON.

TRENDS:
{payload}

Return exactly:
[{{"name":"","visual_prompt":"","visual_rationale":""}}]
"""
    parsed = _parse(generate_response(prompt))[:5]
    if len(parsed) < len(trends[:5]):
        missing = trends[len(parsed):5]
        if missing:
            recovery_payload = json.dumps(missing, indent=2, ensure_ascii=False)
            recovery_prompt = f"""
Create ONE specific realistic editorial AI visualization prompt for EACH trend below.
These are visualizations, not evidence. Keep the same order and return ONLY JSON.
Avoid generic futuristic AI scenes, brands, logos, readable text and statistics.
Show the observable behavior, aesthetic or product/lifestyle pattern directly.

TRENDS:
{recovery_payload}

Return exactly:
[{{"name":"","visual_prompt":"","visual_rationale":""}}]
"""
            try:
                parsed.extend(_parse(generate_response(recovery_prompt))[:len(missing)])
            except Exception:
                pass
    return parsed[:5]
