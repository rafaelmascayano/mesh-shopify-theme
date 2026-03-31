#!/usr/bin/env python3
"""
Generate internal linking strategy for SEO landing pages.
This script creates a map of how to link between:
- Listings to category pages
- Listings to player cluster pages
- Category pages to related category pages
- Player cluster pages to related cluster pages
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError

from app import create_app, db
from app.models import Listing

load_dotenv()


def generate_internal_linking_map():
    """Generate comprehensive internal linking recommendations."""
    app = create_app()

    with app.app_context():
        print("=" * 70)
        print("INTERNAL LINKING STRATEGY - SEO LANDING PAGES")
        print("=" * 70)

        try:
            listings = db.session.query(Listing).filter_by(sold=False).all()

            # 1. Category linking
            categories = {}
            for listing in listings:
                if listing.category_id:
                    if listing.category_id not in categories:
                        categories[listing.category_id] = []
                    categories[listing.category_id].append(listing.id)

            print(f"\n📁 Category Linking Opportunities:")
            print(f"   Found {len(categories)} categories with products")

            # 2. Player count clustering
            player_clusters = {}
            for listing in listings:
                if listing.players_min and listing.players_max:
                    key = f"{listing.players_min}-{listing.players_max}"
                    if key not in player_clusters:
                        player_clusters[key] = []
                    player_clusters[key].append(listing.id)

            print(f"\n👥 Player Cluster Linking Opportunities:")
            for cluster, product_ids in sorted(player_clusters.items()):
                if len(product_ids) >= 3:
                    print(f"   {cluster} players: {len(product_ids)} products → /juegos-mesa-{cluster}")

            print("\n✅ Internal linking map generated")
            return 0

        except SQLAlchemyError as e:
            print(f"❌ Database error: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(generate_internal_linking_map())
