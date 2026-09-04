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
            if isinstance(parsed, dict):
                for key in ("opportunities", "results"):
                    if isinstance(parsed.get(key), list): return parsed[key]
        except json.JSONDecodeError:
            pass
    a,b=cleaned.find("["),cleaned.rfind("]")
    if a>=0 and b>a:
        try:
            parsed=json.loads(cleaned[a:b+1]); return parsed if isinstance(parsed,list) else []
        except json.JSONDecodeError: pass
    return []


def _score(v):
    try: return round(max(0,min(10,float(v))),1)
    except (TypeError,ValueError): return 0.0


def score_opportunities(trends: list[dict]) -> list[dict]:
    payload=json.dumps(trends[:5],indent=2,ensure_ascii=False)
    prompt=f"""
You are AROHA's senior opportunity strategist.

Convert the supplied emerging trends into up to THREE ranked OPPORTUNITY SPACES.
An opportunity is a credible gap, unmet need, underserved behavior, or strategic
possibility exposed by the evidence. It is NOT a finished product, app, campaign,
feature list, or brand concept.

Use only supplied evidence. Do not invent statistics, market size, demand, brands,
consumer facts, or competitors. Separate the levels clearly:
TREND = what is changing.
OPPORTUNITY = where there is room to act because of that change.
CREATIVE = how to express/solve it (handled later).

Score each from 0-10 on evidence_strength, growth_signal, creative_potential and
commercial_potential. Overall score is their arithmetic mean. Prefer opportunities
that are specific enough to act on but broad enough to support multiple solutions.
Keep each visible field concise. Return ONLY valid JSON.

TRENDS:
{payload}

Return exactly:
[{{
  "title":"",
  "description":"one concise opportunity statement",
  "unmet_need":"the gap or unresolved need",
  "trend":"the supporting trend name",
  "evidence_strength":0,
  "growth_signal":0,
  "creative_potential":0,
  "commercial_potential":0,
  "overall_score":0,
  "rationale":"one concise why-now statement"
}}]
"""
    parsed=_parse_json(generate_response(prompt))
    cleaned=[]
    for item in parsed:
        if not isinstance(item,dict) or item.get("error"): continue
        ev=_score(item.get("evidence_strength")); gr=_score(item.get("growth_signal")); cr=_score(item.get("creative_potential")); co=_score(item.get("commercial_potential"))
        overall=round((ev+gr+cr+co)/4,1)
        item.update({"evidence_strength":ev,"growth_signal":gr,"creative_potential":cr,"commercial_potential":co,"overall_score":overall,"score":overall,"opportunity_score":overall,"name":item.get("title","")})
        cleaned.append(item)
    cleaned.sort(key=lambda x:x.get("overall_score",0),reverse=True)
    return cleaned[:3]
