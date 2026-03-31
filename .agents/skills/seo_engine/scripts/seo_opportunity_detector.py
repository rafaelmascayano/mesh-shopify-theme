from collections import defaultdict
from typing import Any


def detect_category_opportunities(
    listings: list[dict[str, Any]], min_cluster_size: int = 2
) -> dict[str, list[str]]:
    """
    Detects programmatic SEO cluster opportunities based on minimum and maximum
    player combinations to recommend new landing pages with enough items.

    Args:
        listings (list[dict[str, Any]]): A list of dictionaries representing products.
        min_cluster_size (int, optional): Minimum required products to form a cluster. Defaults to 2.

    Returns:
        dict[str, list[str]]: An alphabetically sorted dictionary mapping SEO opportunity
            keywords (e.g. 'juegos de mesa para 2 a 4 jugadores') to lists of product titles.
    """
    clusters: dict[str, list[str]] = defaultdict(list)

    for listing in listings:
        title = str(listing.get("title") or "").strip()
        if not title:
            continue

        try:
            pmin = (
                int(listing.get("players_min")) if listing.get("players_min") is not None else None
            )
            pmax = (
                int(listing.get("players_max")) if listing.get("players_max") is not None else None
            )
        except (TypeError, ValueError):
            continue

        if not pmin and not pmax:
            continue

        if pmin and pmax and pmin > 0 and pmax > 0:
            keyword = (
                f"juegos de mesa para {pmin} jugadores"
                if pmin == pmax
                else f"juegos de mesa para {pmin} a {pmax} jugadores"
            )
        elif pmin and pmin > 0:
            keyword = f"juegos de mesa para {pmin} o mas jugadores"
        elif pmax and pmax > 0:
            keyword = f"juegos de mesa para hasta {pmax} jugadores"
        else:
            continue

        if title not in clusters[keyword]:
            clusters[keyword].append(title)

    filtered = {
        keyword: sorted(titles)
        for keyword, titles in clusters.items()
        if len(titles) >= min_cluster_size
    }
    return dict(sorted(filtered.items(), key=lambda item: item[0]))


def analyze_competitor_gap(keyword: str, current_site_url: str | None = None) -> dict[str, Any]:
    """
    Detects competitor pages ranking for important keywords and opportunities
    for new category pages or missing products.
    """
    recommended_page = f"/juegos-de-mesa-{keyword.replace(' ', '-').lower()}"

    return {
        "target_keyword": keyword,
        "recommended_page": current_site_url if current_site_url else recommended_page,
        "expected_search_intent": "commercial",
        "hijacking_strategy": [
            "Use comprehensive FAQ schema targeting SERP questions.",
            "Optimize H1 structure to match exact intent.",
            "Create comprehensive product cluster with internal linking.",
        ],
    }
