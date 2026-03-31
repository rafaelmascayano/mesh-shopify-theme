#!/usr/bin/env python3
"""
Validate SEO markup on key pages.
Run from project root: python scripts/validate_seo_markup.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import json

from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError

from app import create_app, db
from app.models import Listing

load_dotenv()


def validate_seo_markup():
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("SEO MARKUP VALIDATION REPORT")
        print("=" * 60)

        # 1. Check listings with descriptions
        try:
            total_listings = db.session.query(Listing).count()
            active_listings = db.session.query(Listing).filter_by(sold=False).count()
            with_description = (
                db.session.query(Listing)
                .filter(Listing.description.isnot(None), Listing.description != "")
                .count()
            )

            print(f"\nListing Inventory:")
            print(f"  Total listings: {total_listings}")
            print(f"  Active listings: {active_listings}")
            print(f"  With descriptions: {with_description}")
            print(f"  Missing descriptions: {total_listings - with_description}")

            # 2. Check for schema markup readiness
            listings_ready = db.session.query(Listing).filter(
                Listing.description.isnot(None),
                db.func.length(Listing.description) >= 100
            ).count()

            print(f"\nSchema Markup Readiness:")
            print(f"  Listings ready for schema: {listings_ready}")
            print(f"  Coverage: {round(100 * listings_ready / max(1, total_listings), 1)}%")

            print("\n✅ SEO markup validation complete")
            return 0

        except SQLAlchemyError as e:
            print(f"❌ Database error: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(validate_seo_markup())
