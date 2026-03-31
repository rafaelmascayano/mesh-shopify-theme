import json
from typing import Any


def build_product_schema(
    listing: dict[str, Any], reviews: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """
    Builds a JSON-LD Product schema mapping the listing and its reviews if available.

    Args:
        listing (dict[str, Any]): The product listing.
        reviews (list[dict[str, Any]] | None, optional): Optional reviews for aggregate ratings. Defaults to None.

    Returns:
        dict[str, Any]: A dictionary representing the Product schema.
    """
    title = str(listing.get("title") or "").strip() or "Producto"
    description = str(listing.get("description") or "").strip() or "Sin descripcion"
    price = listing.get("price")
    availability = (
        "https://schema.org/OutOfStock" if listing.get("sold") else "https://schema.org/InStock"
    )

    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": title,
        "description": description,
        "offers": {
            "@type": "Offer",
            "price": price if price is not None else 0,
            "priceCurrency": "CLP",
            "availability": availability,
        },
    }

    if reviews:
        ratings = [float(r["rating"]) for r in reviews if "rating" in r and r["rating"] is not None]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": round(avg_rating, 1),
                "reviewCount": len(ratings),
            }
    return schema


def generate_schema(
    listing: dict[str, Any], reviews: list[dict[str, Any]] | None = None, indent: int = 2
) -> str:
    """
    Generates a serialized JSON string of the product schema.

    Args:
        listing (dict[str, Any]): The product listing.
        reviews (list[dict[str, Any]] | None, optional): Optional reviews. Defaults to None.
        indent (int, optional): Formatting indent. Defaults to 2.

    Returns:
        str: A JSON string containing the schema markup.
    """
    return json.dumps(
        build_product_schema(listing, reviews=reviews),
        indent=indent,
        ensure_ascii=False,
    )
