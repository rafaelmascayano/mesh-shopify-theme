from collections import defaultdict
from typing import Any

# Import from relative path to avoid circular imports
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from growth.utils.supabase_client import get_supabase_client


def get_supabase():
    return get_supabase_client()


def get_listings() -> list[dict[str, Any]]:
    response = (
        get_supabase()
        .table("listings")
        .select("id,title,players_min,players_max,category_id")
        .execute()
    )
    return response.data or []


def get_categories() -> dict[str, str]:
    response = get_supabase().table("categories").select("id,slug").execute()
    data = response.data or []
    return {str(c["id"]): str(c["slug"]) for c in data if c.get("id") and c.get("slug")}


def detect_player_clusters(listings: list[dict[str, Any]]) -> dict[str, list[str]]:
    clusters: dict[str, list[str]] = defaultdict(list)
    for listing in listings:
        title = str(listing.get("title") or "").strip()
        if not title:
            continue
        pmin = listing.get("players_min")
        pmax = listing.get("players_max")
        if pmin is None or pmax is None:
            continue
        key = f"{pmin}-{pmax}"
        if title not in clusters[key]:
            clusters[key].append(title)
    return dict(sorted((k, sorted(v)) for k, v in clusters.items()))


def scan_opportunities():
    """Scan entire database for programmatic SEO opportunities."""
    print("=" * 70)
    print("SEO AUTOPILOT - PROGRAMMATIC OPPORTUNITY SCANNER")
    print("=" * 70)

    listings = get_listings()
    categories = get_categories()
    clusters = detect_player_clusters(listings)

    print(f"\n📊 Listing Inventory:")
    print(f"   Total listings: {len(listings)}")
    print(f"   Categories: {len(categories)}")
    print(f"   Player clusters: {len(clusters)}")

    print(f"\n🎯 Programmatic SEO Opportunities:")
    for cluster, games in clusters.items():
        if len(games) >= 3:
            print(f"   [{cluster} players] {len(games)} games → /juegos-mesa-{cluster}")

    return {
        "listings": len(listings),
        "categories": len(categories),
        "clusters": len(clusters),
        "opportunities": {k: len(v) for k, v in clusters.items() if len(v) >= 3}
    }


if __name__ == "__main__":
    scan_opportunities()
