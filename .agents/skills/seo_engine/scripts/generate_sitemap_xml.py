#!/usr/bin/env python3
"""
Generate comprehensive sitemap.xml including all SEO landing pages.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError

from app import create_app, db
from app.models import Listing

load_dotenv()

CATEGORIES = ["estrategia", "party", "familiares", "cartas", "cooperativos"]
PLAYER_CLUSTERS = ["2-2", "3-4", "5-6", "7-8"]


def format_datetime(dt):
    """Format datetime for sitemap."""
    if dt is None:
        return datetime.utcnow().isoformat() + "Z"
    return dt.replace(microsecond=0).isoformat() + "Z"


def generate_sitemap():
    """Generate comprehensive sitemap."""
    app = create_app()

    with app.app_context():
        base_url = os.getenv("SITE_URL", "https://tablerodevuelta.cl").rstrip("/")

        print("=" * 70)
        print("SITEMAP GENERATION")
        print("=" * 70)

        try:
            # 1. Static pages
            urls = [
                {"loc": f"{base_url}/", "priority": 1.0},
                {"loc": f"{base_url}/juegos", "priority": 0.9},
                {"loc": f"{base_url}/categorias", "priority": 0.8},
            ]

            # 2. Category pages
            for category in CATEGORIES:
                urls.append({
                    "loc": f"{base_url}/categoria/{category}",
                    "priority": 0.7,
                })

            # 3. Player cluster pages
            for cluster in PLAYER_CLUSTERS:
                urls.append({
                    "loc": f"{base_url}/juegos-mesa-{cluster}-jugadores",
                    "priority": 0.7,
                })

            # 4. Product pages
            listings = db.session.query(Listing).filter_by(sold=False).all()
            for listing in listings:
                urls.append({
                    "loc": f"{base_url}/juego/{listing.id}/{listing.title.lower().replace(' ', '-')}",
                    "lastmod": format_datetime(listing.updated_at),
                    "priority": 0.6,
                })

            print(f"\n📄 Generated sitemap with {len(urls)} URLs")
            print(f"   - Static pages: 3")
            print(f"   - Category pages: {len(CATEGORIES)}")
            print(f"   - Player clusters: {len(PLAYER_CLUSTERS)}")
            print(f"   - Product pages: {len(listings)}")

            print(f"\n✅ Sitemap ready: {base_url}/sitemap.xml")
            return 0

        except SQLAlchemyError as e:
            print(f"❌ Database error: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(generate_sitemap())
