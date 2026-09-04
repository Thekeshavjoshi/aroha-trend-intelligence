import json
import re
from src.llm.client import generate_response


def _parse_json(response):
    if not response:
        return []
    cleaned = re.sub(r"```(?:json)?\s*|```", "", response.strip(), flags=re.I).strip()
    for candidate in (response.strip(), cleaned):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list): return parsed
            if isinstance(parsed, dict) and isinstance(parsed.get("visual_prompts"), list): return parsed["visual_prompts"]
        except json.JSONDecodeError:
            pass
    a, b = cleaned.find("["), cleaned.rfind("]")
    if a >= 0 and b > a:
        try:
            parsed = json.loads(cleaned[a:b+1]); return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError: pass
    return []


def generate_visual_prompts(directions: list[dict]) -> list[dict]:
    payload = json.dumps(directions[:3], indent=2, ensure_ascii=False)
    prompt = f"""
You are AROHA's senior visual concept director.

Convert each creative direction into ONE production-ready FLUX prompt. The image must communicate the selected opportunity at a glance.
Specify subject/product, people/styling when relevant, environment, composition/camera, materials, restrained palette, lighting, mood and commercial/editorial style.

Rules:
- Stay faithful to the input.
- Do not invent facts, brands, logos, slogans, watermarks or text-heavy UI.
- Keep products brand-neutral.
- Avoid generic futuristic AI imagery.
- Avoid readable text inside the scene.
- Make each prompt visually distinct.
- Return ONLY valid JSON.

CREATIVE DIRECTIONS:
{payload}

Return exactly:
[{{"name":"","visual_prompt":"","visual_rationale":""}}]
"""
    parsed = _parse_json(generate_response(prompt))[:3]

    # Recovery pass: if the model returned fewer prompts than directions,
    # generate only the missing concepts. This keeps the Opportunity ->
    # Creative -> Visual pipeline one-to-one without changing successful output.
    if len(parsed) < len(directions[:3]):
        missing = directions[len(parsed):3]
        if missing:
            recovery_payload = json.dumps(missing, indent=2, ensure_ascii=False)
            recovery_prompt = f"""
Create ONE concise FLUX-ready visual prompt for EACH creative direction below.
Return ONLY valid JSON as a list. Keep the same order. Do not invent brands, statistics,
logos, readable text or unsupported facts. Make the scene commercially useful and specific.

CREATIVE DIRECTIONS:
{recovery_payload}

Return exactly:
[{{"name":"","visual_prompt":"","visual_rationale":""}}]
"""
            try:
                parsed.extend(_parse_json(generate_response(recovery_prompt))[:len(missing)])
            except Exception:
                pass

    return parsed[:3]
