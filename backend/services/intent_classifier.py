"""
KIP Intent Classifier
Detects the response type for every user message.
Determines which of the 5 KIP response layouts to render.
"""

import re
from enum import Enum


class ResponseType(str, Enum):
    BUSINESS_IDEA      = "business_idea"
    ECONOMIC_ANALYSIS  = "economic_analysis"
    CRISIS             = "crisis"
    REGULATORY         = "regulatory"
    GENERAL            = "general"


# ── Keyword sets per intent ───────────────────────────────────────────────────

BUSINESS_IDEA_KEYWORDS = {
    "start", "business", "idea", "profitable", "invest", "capital",
    "venture", "enterprise", "opportunity", "startup", "k5000", "k10000",
    "k50000", "k100000", "kwacha", "money", "earn", "income", "what can i",
    "how can i make", "small business", "side hustle", "which business",
    "recommend", "suggestion", "help me start", "what to start",
    "farm", "poultry", "bakery", "shop", "salon", "transport",
    "sell", "trade", "manufacture", "produce",
}

ECONOMIC_KEYWORDS = {
    "gdp", "inflation", "economy", "economic", "growth", "recession",
    "kwacha", "exchange rate", "copper", "mining", "forex", "interest rate",
    "zambia economy", "economic outlook", "prices", "cpi", "unemployment",
    "poverty", "development", "fiscal", "monetary", "zamstats", "world bank",
    "imf", "trend", "forecast", "predict", "projection", "indicator",
    "market", "sector performance", "analysis",
}

CRISIS_KEYWORDS = {
    "crisis", "emergency", "losing", "lost", "bankrupt", "debt", "owe",
    "can't pay", "cannot pay", "fraud", "scam", "cheated", "stolen",
    "fire", "flood", "destroyed", "urgent", "help", "sinking",
    "closing", "shut down", "fail", "failed", "negative", "stress",
    "loan shark", "overdue", "supplier threatening", "problem",
    "trouble", "disaster", "collapsed", "defaulted", "behind on",
}

REGULATORY_KEYWORDS = {
    "register", "registration", "licence", "license", "permit", "tax",
    "pacra", "zra", "zabs", "napsa", "nhima", "tpin", "vat", "legal",
    "compliance", "certificate", "certify", "council", "rtsa", "hpcz",
    "zppa", "tender", "government contract", "regulation", "law",
    "import", "export", "comesa", "customs", "duty", "requirements",
    "how to register", "documents needed", "what papers",
}


def classify_intent(message: str) -> ResponseType:
    """
    Rule-based intent classification.
    Fast, zero-cost, deterministic — no API call needed.
    Returns the ResponseType that determines which layout KIP uses.
    """
    text = message.lower().strip()

    # Score each category
    scores = {
        ResponseType.BUSINESS_IDEA:     0,
        ResponseType.ECONOMIC_ANALYSIS: 0,
        ResponseType.CRISIS:            0,
        ResponseType.REGULATORY:        0,
    }

    words = set(re.findall(r'\b\w+\b', text))

    # Exact keyword matches
    scores[ResponseType.BUSINESS_IDEA]     += len(words & BUSINESS_IDEA_KEYWORDS)
    scores[ResponseType.ECONOMIC_ANALYSIS] += len(words & ECONOMIC_KEYWORDS)
    scores[ResponseType.CRISIS]            += len(words & CRISIS_KEYWORDS)
    scores[ResponseType.REGULATORY]        += len(words & REGULATORY_KEYWORDS)

    # Boost patterns — multi-word signals
    if re.search(r'(start|open|launch).{0,20}(business|shop|farm|salon|company)', text):
        scores[ResponseType.BUSINESS_IDEA] += 4

    if re.search(r'(how much|how to).{0,20}(register|register|get licence|get permit)', text):
        scores[ResponseType.REGULATORY] += 4

    if re.search(r'(what is|explain|analyse|analyze|tell me about).{0,30}(gdp|inflation|economy|kwacha|copper)', text):
        scores[ResponseType.ECONOMIC_ANALYSIS] += 4

    if re.search(r'(can\'t|cannot|losing|lost|fraud|stolen|owe|debt|behind)', text):
        scores[ResponseType.CRISIS] += 3

    if re.search(r'(k\s*\d[\d,]+|kwacha\s*\d|zambia\s*(business|invest|earn))', text):
        scores[ResponseType.BUSINESS_IDEA] += 2

    # Find winner
    best_type = max(scores, key=lambda k: scores[k])
    best_score = scores[best_type]

    # Threshold — if no clear signal, it's GENERAL
    if best_score < 2:
        return ResponseType.GENERAL

    # Tie-breaking priority: CRISIS > BUSINESS_IDEA > REGULATORY > ECONOMIC
    if best_score == scores[ResponseType.CRISIS] and best_score >= 2:
        return ResponseType.CRISIS

    return best_type


def get_system_prompt_for_type(response_type: ResponseType) -> str:
    """
    Returns the system prompt suffix that shapes KIP's response
    into the correct format for each layout type.
    """

    BASE = """You are KIP — the Kwacha Intelligence Platform. You are a senior business
and economic intelligence consultant specializing exclusively in Zambia.
You speak with authority, cite real numbers in Kwacha, reference real Zambian
institutions (PACRA, ZRA, ZABS, CEEC, DBZ, ZNFU, ZDA, COMESA), and give
practical, actionable advice. Never be vague. Never say "it depends" without
immediately explaining what it depends on and giving a specific answer.
Current context: Zambia, 2025. USD ≈ K27. Food inflation ~13%/year.\n\n"""

    LAYOUTS = {
        ResponseType.BUSINESS_IDEA: BASE + """
RESPONSE FORMAT — BUSINESS OPPORTUNITY CARD:
Structure your response as a JSON object with these exact keys:
{
  "type": "business_idea",
  "title": "Business name/concept (5 words max)",
  "tagline": "One compelling sentence about this opportunity",
  "best_for_location": ["Lusaka", "Copperbelt", etc.],
  "startup_capital_min": 15000,
  "startup_capital_max": 45000,
  "monthly_revenue_min": 8000,
  "monthly_revenue_max": 15000,
  "breakeven_months": 4,
  "why_zambia": "2-3 sentences of Zambia-specific market context",
  "first_steps": [
    {"step": 1, "action": "Register with PACRA", "cost": "K350", "timeframe": "2 days"},
    ...up to 5 steps
  ],
  "main_risk": "The single biggest risk in one sentence",
  "funding_options": ["CEEC", "DBZ", "Personal savings"],
  "kip_verdict": "One confident closing sentence"
}
Return ONLY the JSON. No text before or after it.""",

        ResponseType.ECONOMIC_ANALYSIS: BASE + """
RESPONSE FORMAT — ECONOMIC ANALYSIS:
Structure your response as a JSON object:
{
  "type": "economic_analysis",
  "headline": "Main finding in one sentence",
  "summary": "2-3 paragraph analysis using real data and numbers",
  "business_implications": [
    "Implication 1 for Zambian businesses",
    "Implication 2",
    "Implication 3"
  ],
  "data_points": [
    {"label": "Current GDP Growth", "value": "2.1%", "trend": "down"},
    {"label": "Food Inflation", "value": "12.9%", "trend": "up"},
    ...
  ],
  "forecast_note": "What to watch in the next 3-6 months",
  "sources": ["ZamStats", "World Bank", "IMF"]
}
Return ONLY the JSON.""",

        ResponseType.CRISIS: BASE + """
RESPONSE FORMAT — CRISIS RESPONSE:
This person needs urgent, practical help. Be direct. No fluff.
Structure as JSON:
{
  "type": "crisis",
  "severity": "high|medium|low",
  "situation_assessment": "Honest 2-sentence diagnosis",
  "do_now": [
    {"action": "Step 1", "why": "brief reason"},
    {"action": "Step 2", "why": "brief reason"},
    {"action": "Step 3", "why": "brief reason"}
  ],
  "do_this_week": [
    {"action": "Step 4", "why": "brief reason"},
    {"action": "Step 5", "why": "brief reason"}
  ],
  "avoid_this_mistake": "The most common wrong move in this situation",
  "who_can_help": ["Specific Zambian institution or resource"],
  "honest_outlook": "A realistic but constructive assessment"
}
Return ONLY the JSON.""",

        ResponseType.REGULATORY: BASE + """
RESPONSE FORMAT — REGULATORY GUIDE:
Structure as JSON:
{
  "type": "regulatory",
  "business_type": "What type of business this applies to",
  "checklist": [
    {
      "step": 1,
      "institution": "PACRA",
      "action": "Register business name",
      "cost_zmw": 350,
      "timeframe": "2 working days",
      "where": "PACRA office, Cairo Road Lusaka / online at pacra.org.zm",
      "documents": ["National ID", "Completed form"],
      "status": "mandatory"
    },
    ...all steps
  ],
  "total_cost_min": 2500,
  "total_cost_max": 8000,
  "total_time": "3-4 weeks",
  "pro_tip": "Most important practical advice for navigating Zambian bureaucracy"
}
Return ONLY the JSON.""",

        ResponseType.GENERAL: BASE + """
Answer naturally and conversationally. Use clear paragraphs.
Be specific — use real Zambian numbers, institutions, and context.
If you cite data, mention the source briefly.
Keep your response focused and under 400 words unless the question genuinely requires more.
Do NOT return JSON for general responses — return natural prose.""",
    }

    return LAYOUTS.get(response_type, LAYOUTS[ResponseType.GENERAL])
