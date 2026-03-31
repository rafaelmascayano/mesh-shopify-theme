from typing import Any


def audit_listing_seo(listing: dict[str, Any]) -> dict[str, Any]:
    """
    Audits a single listing for SEO quality and identifies issues.

    Args:
        listing (dict[str, Any]): Product listing to audit.

    Returns:
        dict[str, Any]: Audit results with issues and score.
    """
    issues = []
    score = 100

    # Check title
    title = str(listing.get("title") or "").strip()
    if not title or len(title) < 3:
        issues.append({"type": "title", "message": "Title is missing or too short"})
        score -= 20
    elif len(title) > 100:
        issues.append({"type": "title", "message": "Title is too long (>100 chars)"})
        score -= 5

    # Check description
    description = str(listing.get("description") or "").strip()
    if not description or len(description) < 50:
        issues.append({"type": "description", "message": "Description is missing or too short (<50 chars)"})
        score -= 30
    elif len(description) > 2000:
        issues.append({"type": "description", "message": "Description is too long (>2000 chars)"})
        score -= 5

    # Check player count
    players_min = listing.get("players_min")
    players_max = listing.get("players_max")
    if not players_min and not players_max:
        issues.append({"type": "players", "message": "Player count is missing"})
        score -= 15

    # Check price
    if listing.get("price") is None or listing.get("price") <= 0:
        issues.append({"type": "price", "message": "Price is missing or invalid"})
        score -= 10

    return {
        "listing_id": listing.get("id"),
        "title": title,
        "seo_score": max(0, score),
        "issues": issues,
        "recommendations": [
            issue.get("message") for issue in issues
        ]
    }
