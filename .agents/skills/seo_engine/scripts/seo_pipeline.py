from typing import Any
from .seo_description_generator import generate_seo_description
from .product_faq_generator import generate_faq, generate_faq_schema
from .schema_generator import build_product_schema
from .listings_seo_audit import audit_listing_seo


def run_seo_pipeline_for_listing(listing: dict[str, Any]) -> dict[str, Any]:
    """
    Aggregate SEO metrics, opportunities, schemas, and descriptions
    for a single product in a stable JSON payload.

    Args:
        listing (dict[str, Any]): Product listing to process.

    Returns:
        dict[str, Any]: Aggregated SEO analysis and recommendations.
    """
    audit = audit_listing_seo(listing)
    description = generate_seo_description(listing)
    faq = generate_faq(listing)
    faq_schema = generate_faq_schema(listing)
    product_schema = build_product_schema(listing)

    return {
        "listing_id": listing.get("id"),
        "title": listing.get("title"),
        "audit": audit,
        "generated_description": description,
        "generated_faq": faq,
        "faq_schema": faq_schema,
        "product_schema": product_schema,
        "recommendations": [
            "Apply generated description to listing",
            "Add FAQ section to product page",
            "Include Product and FAQPage schema markup",
        ] + audit.get("recommendations", [])
    }
