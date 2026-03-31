#!/usr/bin/env python3
"""
Generate and apply SEO descriptions to listings without descriptions.
Run from project root: python scripts/apply_seo_descriptions.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from app import create_app, db
from app.models import Listing
from scripts.seo_description_generator import generate_seo_description
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

def apply_seo_descriptions():
    app = create_app()

    with app.app_context():
        try:
            # Find listings without descriptions or with very short descriptions
            listings_to_update = Listing.query.filter(
                (Listing.description.is_(None)) |
                (Listing.description == '') |
                (db.func.length(Listing.description) < 50)
            ).all()

            print(f"Found {len(listings_to_update)} listings to update")

            updated_count = 0
            for listing in listings_to_update:
                listing_dict = {
                    "title": listing.title,
                    "players_min": listing.players_min,
                    "players_max": listing.players_max,
                }

                seo_desc = generate_seo_description(listing_dict)

                if not listing.description or len(listing.description or "") < 50:
                    listing.description = seo_desc
                    updated_count += 1
                    print(f"  ✓ {listing.title} - {len(seo_desc)} chars")

            db.session.commit()
            print(f"\n✅ Updated {updated_count} listings with SEO descriptions")

        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"❌ Database error: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(apply_seo_descriptions())
