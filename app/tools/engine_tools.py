from __future__ import annotations
import hashlib
from app.models import SavingsBand, FeasibilityScore
from app.tools.retrieval import retrieve_material, get_market_rules

def compute_savings_band(idea: dict, market: str) -> SavingsBand:
    component = idea.get("component") or ""
    material = retrieve_material(component, market)
    if not material:
        return SavingsBand(low_dkk=0, mid_dkk=0, high_dkk=0, method="fallback_no_material_data", data_quality="low")
    annual_spend = sum(float(r.get("unit_cost_dkk", 0) or 0) * float(r.get("annual_units", 0) or 0) for r in material)
    text = idea.get("cleaned_en", "").lower()
    factor = 0.03
    data_quality = "medium"
    if "gauge" in text: factor = 0.11
    if "printing" in text or "label" in text: factor = 0.015
    if "bio-pe" in text: factor = -0.02; data_quality = "medium_negative_saving"
    if "neck finish" in text or "standardise" in text or "standardize" in text: factor = 0.04
    if "bottle" in text and "weight" in text: factor = 0.055
    mid = annual_spend * factor
    return SavingsBand(low_dkk=round(mid*0.7, 2), mid_dkk=round(mid, 2), high_dkk=round(mid*1.3, 2), method="material_spend_sensitivity", data_quality=data_quality)

def score_feasibility(idea: dict, market: str) -> FeasibilityScore:
    text = idea.get("cleaned_en", "").lower()
    score = 75
    reasons: list[str] = []
    hits: list[str] = []
    for rule in get_market_rules(market):
        constraint = rule["constraint"].lower()
        category = rule.get("category", "")
        hit = False
        if "carton" in text and "carton" in constraint:
            hit = True
        if "tray" in text and "tray" in constraint:
            hit = True
        if ("label" in text or "abv" in text or "wort" in text) and ("label" in constraint or "abv" in constraint or "wort" in constraint):
            hit = True
        if hit:
            severity = 35 if rule.get("hardness") == "hard_constraint" else 20
            score -= severity
            hits.append(rule["rule_id"])
            reasons.append(f"market_rule:{rule['rule_id']}:{category}")
    if "cap" in text or "tooling" in text or "pull-tab" in text:
        score -= 20; reasons.append("possible_capex_or_tooling")
    if "bio-pe" in text:
        score -= 10; reasons.append("supplier_qualification_needed")
    if "gauge" in text and market == "CN":
        score -= 15; reasons.append("premium_perception_risk")
    if "zero" in text or "no material" in text:
        score -= 10
    return FeasibilityScore(score=max(0, min(100, score)), reason_codes=reasons or ["no_major_blocker"], market_rule_hits=hits)

def generate_alternatives(idea: dict, n: int = 3) -> list[str]:
    base = idea.get("cleaned_en", "idea")
    return [
        f"Pilot smaller SKU subset for: {base}",
        f"Negotiate supplier quote before full rollout for: {base}",
        f"Run A/B market validation before implementing: {base}",
    ][:n]

def deterministic_duplicate_key(cleaned_en: str) -> str:
    text = cleaned_en.lower()
    semantic_groups = {
        "330ml can gauge": ["330", "can", "gauge"],
        "neck finish 202": ["neck", "202"],
        "carton tray": ["carton", "tray"],
        "shrink film": ["shrink", "film"],
        "cap 26mm 24mm": ["cap", "24mm"],
    }
    for group, req in semantic_groups.items():
        if all(t in text for t in req):
            return hashlib.md5(group.encode()).hexdigest()[:8]
    return hashlib.md5(" ".join(sorted(text.split())).encode()).hexdigest()[:8]
