"""
AI-powered natural language parser for trip planning input.

Uses the Groq API (free forever — no credit card required) to extract
structured trip data from free-form text using Llama 3.

Get a free API key at: https://console.groq.com
  1. Sign up / log in
  2. Go to API Keys → Create API Key
  3. Copy the key starting with "gsk_..."

Falls back to a keyword-based parser when no key is provided or call fails.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import List, Literal, Optional

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

BudgetLevel = Literal["low", "medium", "high"]

_BUDGET_MAP: dict[str, int] = {
    "low":    5_000,
    "medium": 15_000,
    "high":   40_000,
}

SUPPORTED_CITIES = {"Cairo", "Alexandria"}

PREFERENCE_KEYWORDS = {
    "food":     ["food", "eat", "restaurant", "dining", "cuisine", "seafood",
                 "street food", "cafe", "coffee", "brunch"],
    "culture":  ["culture", "museum", "history", "historical", "heritage",
                 "ancient", "mosque", "church", "religious", "tour",
                 "monument", "archaeological", "coptic", "islamic"],
    "shopping": ["shop", "shopping", "mall", "market", "bazaar", "souvenir",
                 "buy", "store"],
}

# Groq — OpenAI-compatible, free forever
_GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL = "llama-3.1-8b-instant"


@dataclass
class ParsedTrip:
    cities: List[str] = field(default_factory=list)
    budget_level: BudgetLevel = "medium"
    budget_egp: int = 15_000
    num_days: int = 3
    preferences: List[str] = field(default_factory=list)
    raw_summary: str = ""
    used_fallback: bool = False
    fallback_reason: str = ""


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
Extract trip data from the user message. Reply ONLY with valid JSON, no extra text.

Schema: {"cities":[string],"budget_level":"low"|"medium"|"high","budget_egp":integer,"num_days":integer,"preferences":[string],"raw_summary":string}

- cities: "Cairo" or "Alexandria" only. Default ["Cairo"].
- budget_level: low<8000, medium 8000-25000, high>25000. Convert 5k=5000. Default medium.
- num_days: week=7, month=30. Sum all day mentions. Default 3.
- preferences: from ["food","culture","shopping"] only. [] if none.
- raw_summary: one friendly sentence.
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_trip_input(user_text: str, api_key: Optional[str] = None) -> ParsedTrip:
    """
    Parse user_text using Groq (Llama 3) and return a ParsedTrip.
    Falls back to offline keyword parsing if the key is missing or call fails.
    api_key defaults to the GROQ_API_KEY environment variable.
    """
    key = api_key or os.environ.get("GROQ_API_KEY", "")
    if key:
        try:
            return _call_groq(user_text, key)
        except Exception as exc:
            reason = _classify_error(exc)
            print(f"[ai_parser] Groq call failed: {reason}")
            result = _fallback_parse(user_text)
            result.fallback_reason = reason
            return result

    result = _fallback_parse(user_text)
    result.fallback_reason = "No API key provided"
    return result


# ---------------------------------------------------------------------------
# Groq call  (OpenAI-compatible)
# ---------------------------------------------------------------------------

def _call_groq(user_text: str, api_key: str) -> ParsedTrip:
    """Call Groq via the OpenAI-compatible endpoint."""
    import urllib.request

    payload = json.dumps({
        "model": _GROQ_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": user_text},
        ],
        "temperature": 0,
        "max_tokens": 300,
    }).encode()

    req = urllib.request.Request(
        _GROQ_URL,
        data=payload,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=20) as resp:
        body = json.loads(resp.read())

    content = body["choices"][0]["message"]["content"].strip()

    # Strip accidental markdown fences
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()

    data = json.loads(content)
    return _dict_to_parsed_trip(data, used_fallback=False)


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

def _classify_error(exc: Exception) -> str:
    msg = str(exc)
    if "401" in msg:
        return "Invalid API key (HTTP 401) — check your key at console.groq.com"
    if "429" in msg:
        return "Rate limit (HTTP 429) — free tier limit reached, wait a moment"
    if "404" in msg:
        return "Model not found (HTTP 404) — model name may have changed"
    if "400" in msg:
        return "Bad request (HTTP 400) — check your input"
    if "getaddrinfo" in msg or "Name or service" in msg:
        return "No internet / network blocked"
    if "timed out" in msg.lower() or "timeout" in msg.lower():
        return "Request timed out — try again"
    return f"{type(exc).__name__}: {msg}"


# ---------------------------------------------------------------------------
# Offline keyword fallback
# ---------------------------------------------------------------------------

def _fallback_parse(text: str) -> ParsedTrip:
    """Rule-based extraction used when Groq is unavailable."""
    lower = text.lower()

    # Cities
    cities: List[str] = []
    for city in SUPPORTED_CITIES:
        if city.lower() in lower:
            cities.append(city)
    if not cities:
        cities = ["Cairo"]

    def _parse_amount(raw: str) -> int:
        raw = raw.replace(",", "").strip()
        m = re.match(r"^(\d+(?:\.\d+)?)\s*k$", raw, re.IGNORECASE)
        if m:
            return int(float(m.group(1)) * 1_000)
        return int(float(raw))

    def _level_from_egp(egp: int) -> BudgetLevel:
        if egp < 8_000:   return "low"
        if egp <= 25_000: return "medium"
        return "high"

    # Budget — explicit amount first
    budget_egp: int = 0
    amount_pattern = re.search(
        r"(\d[\d,]*(?:\.\d+)?\s*k?)\s*(?:egp|le|pounds?|جنيه)",
        lower, re.IGNORECASE,
    )
    if not amount_pattern:
        amount_pattern = re.search(
            r"budget\s+(?:of\s+|is\s+|around\s+)?(\d[\d,]*(?:\.\d+)?\s*k)",
            lower, re.IGNORECASE,
        )

    if amount_pattern:
        budget_egp = _parse_amount(amount_pattern.group(1))
        budget_level: BudgetLevel = _level_from_egp(budget_egp)
    else:
        budget_level = "medium"
        budget_egp = _BUDGET_MAP["medium"]
        if any(w in lower for w in ("cheap", "low budget", "budget trip", "affordable")):
            budget_level = "low"
            budget_egp = _BUDGET_MAP["low"]
        elif any(w in lower for w in ("luxury", "high budget", "expensive", "rich", "premium")):
            budget_level = "high"
            budget_egp = _BUDGET_MAP["high"]

    # Days — sum all mentions
    num_days = 3
    day_map = {"month": 30, "week": 7, "fortnight": 14}
    for word, val in day_map.items():
        if word in lower:
            num_days = val
            break
    else:
        all_days = re.findall(r"(\d+)\s*(?:days?|nights?)", lower)
        if all_days:
            num_days = max(1, min(30, sum(int(d) for d in all_days)))

    # Preferences
    preferences: List[str] = []
    for pref, keywords in PREFERENCE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            preferences.append(pref)

    summary = (
        f"Parsed (offline): {num_days} day(s) in {', '.join(cities)} "
        f"with {budget_level} budget ({budget_egp:,} EGP)"
        + (f", interests: {', '.join(preferences)}" if preferences else "")
        + "."
    )

    return ParsedTrip(
        cities=cities,
        budget_level=budget_level,
        budget_egp=budget_egp,
        num_days=num_days,
        preferences=preferences,
        raw_summary=summary,
        used_fallback=True,
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _dict_to_parsed_trip(data: dict, *, used_fallback: bool) -> ParsedTrip:
    cities = [c for c in data.get("cities", ["Cairo"]) if c in SUPPORTED_CITIES]
    if not cities:
        cities = ["Cairo"]

    budget_level = data.get("budget_level", "medium")
    if budget_level not in ("low", "medium", "high"):
        budget_level = "medium"

    budget_egp  = int(data.get("budget_egp", _BUDGET_MAP[budget_level]))
    num_days    = max(1, min(30, int(data.get("num_days", 3))))
    raw_prefs   = data.get("preferences", [])
    preferences = [p for p in raw_prefs if p in ("food", "culture", "shopping")]

    return ParsedTrip(
        cities=cities,
        budget_level=budget_level,
        budget_egp=budget_egp,
        num_days=num_days,
        preferences=preferences,
        raw_summary=data.get("raw_summary", ""),
        used_fallback=used_fallback,
    )
