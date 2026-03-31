"""SEO Engine scripts for product optimization and analysis."""

from .seo_description_generator import generate_seo_description
from .product_faq_generator import generate_faq, generate_faq_schema
from .schema_generator import build_product_schema, generate_schema
from .seo_opportunity_detector import detect_category_opportunities, analyze_competitor_gap
from .serp_scraper import scrape_serp_for_keyword
from .listings_seo_audit import audit_listing_seo
from .seo_pipeline import run_seo_pipeline_for_listing
from .validate_seo_markup import validate_seo_markup
from .generate_internal_linking import generate_internal_linking_map
from .generate_sitemap_xml import generate_sitemap

__all__ = [
    "generate_seo_description",
    "generate_faq",
    "generate_faq_schema",
    "build_product_schema",
    "generate_schema",
    "detect_category_opportunities",
    "analyze_competitor_gap",
    "scrape_serp_for_keyword",
    "audit_listing_seo",
    "run_seo_pipeline_for_listing",
    "validate_seo_markup",
    "generate_internal_linking_map",
    "generate_sitemap",
]
