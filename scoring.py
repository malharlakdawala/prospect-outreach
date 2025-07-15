"""Score prospects to prioritize outreach."""


def score_prospect(prospect: dict) -> float:
    score = 5.0

    # Company size
    employees = prospect.get("employee_count", 0)
    if 50 <= employees <= 500:
        score += 2.0
    elif 500 < employees <= 5000:
        score += 1.5
    elif employees > 5000:
        score += 0.5

    # Title seniority
    title = (prospect.get("title") or "").lower()
    senior_titles = ["cto", "ceo", "vp", "head of", "director", "founder"]
    if any(t in title for t in senior_titles):
        score += 2.0

    # Has LinkedIn
    if prospect.get("linkedin_url"):
        score += 0.5

    # Industry match
    target_industries = ["technology", "saas", "software", "fintech"]
    industry = (prospect.get("industry") or "").lower()
    if any(ind in industry for ind in target_industries):
        score += 1.5

    return min(score, 10.0)


def rank_prospects(prospects: list[dict]) -> list[dict]:
    for p in prospects:
        p["outreach_score"] = score_prospect(p)
    return sorted(prospects, key=lambda p: p["outreach_score"], reverse=True)
