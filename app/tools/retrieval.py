from __future__ import annotations
import re
import pandas as pd
from pathlib import Path
from app.storage.db import list_rules

DATA_DIR = Path("data")

def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_\.]+", text.lower()))

def extract_context(cleaned_en: str, market: str, brand: str | None = None) -> dict:
    t = cleaned_en.lower()
    component = None
    if "330ml" in t and "can" in t:
        component = "can_330ml"
    elif "500ml" in t and "bottle" in t:
        component = "bottle_500ml"
    elif "carton" in t:
        component = "carton"
    elif "cap" in t or "pull-tab" in t:
        component = "cap"
    elif "shrink" in t or "film" in t:
        component = "shrink_film"
    action = "reduce" if any(x in t for x in ["reduce", "remove", "change", "switch", "standardise", "standardize"]) else "review"
    return {"market": market, "brand": brand, "component": component, "sku_range": component, "action": action}

def retrieve_material(sku_or_component: str | None, market: str) -> list[dict]:
    df = pd.read_csv(DATA_DIR / "material_master.csv")
    mask = (df.market == market)
    if sku_or_component:
        mask &= df.packaging_component.fillna("").str.contains(sku_or_component, case=False, regex=False) | df.sku_code.fillna("").str.contains(sku_or_component, case=False, regex=False)
    return df[mask].to_dict("records")

def find_similar_ideas(query: str, market: str, k: int = 5) -> list[dict]:
    rows = pd.read_csv(DATA_DIR / "raw_workshop_ideas.csv").to_dict("records")
    qtok = tokens(query)
    scored = []
    for row in rows:
        score = len(qtok & tokens(str(row["raw_text"])))
        translated_tokens = tokens(str(row.get("cleaned_en", "")))
        score += len(qtok & translated_tokens)
        if score:
            scored.append({**row, "score": score, "scope": "same_market" if row["market"] == market else "cross_market"})
    return sorted(scored, key=lambda r: (r["scope"] != "same_market", -r["score"]))[:k]

def get_market_rules(market: str, include_expired: bool = False) -> list[dict]:
    return list_rules(market, include_expired=include_expired)

def rule_review_due(market: str, review_window_days: int = 60) -> list[dict]:
    from datetime import date, datetime, timedelta
    cutoff = date.today() + timedelta(days=review_window_days)
    due = []
    for rule in get_market_rules(market, include_expired=True):
        valid_to = rule.get("valid_to")
        if valid_to:
            try:
                if datetime.strptime(valid_to, "%Y-%m-%d").date() <= cutoff:
                    due.append(rule)
            except ValueError:
                pass
    return due
