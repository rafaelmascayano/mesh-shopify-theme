from typing import Any


def _normalize_title(raw_title: Any) -> str:
    title = str(raw_title or "").strip()
    return title or "este juego"


def _players_answer(players_min: Any, players_max: Any, title: str) -> str:
    try:
        pmin = int(players_min) if players_min is not None else None
        pmax = int(players_max) if players_max is not None else None
    except (TypeError, ValueError):
        return f"{title} admite distintos rangos de jugadores segun la edicion."

    if pmin and pmax and pmin > 0 and pmax > 0:
        if pmin == pmax:
            return f"{title} esta pensado para {pmin} jugador{'es' if pmin != 1 else ''}."
        return f"{title} se puede jugar entre {pmin} y {pmax} jugadores."
    if pmin and pmin > 0:
        return f"{title} funciona bien desde {pmin} jugadores."
    if pmax and pmax > 0:
        return f"{title} se suele jugar hasta {pmax} jugadores."
    return f"{title} admite distintos rangos de jugadores segun la mesa."


def generate_faq(
    listing: dict[str, Any], legacy_flat: bool = False
) -> list[dict[str, str]] | list[str]:
    """
    Generates SEO-optimized FAQs based on search intent and player count data.

    Args:
        listing (dict[str, Any]): Dictionary containing product data.
        legacy_flat (bool, optional): Whether to return a flat list of strings. Defaults to False.

    Returns:
        list[dict[str, str]] | list[str]: List of dictionaries containing "question" and "answer" keys.
    """
    title = _normalize_title(listing.get("title"))
    players_min = listing.get("players_min")
    players_max = listing.get("players_max")

    faq = [
        {
            "question": f"Cuantos jugadores pueden jugar {title}?",
            "answer": _players_answer(players_min, players_max, title),
        },
        {
            "question": f"{title} es facil de aprender?",
            "answer": f"La complejidad de {title} varia segun la edicion. Generalmente es accesible para nuevos jugadores.",
        },
        {
            "question": f"Cuanto dura una partida de {title}?",
            "answer": f"La duracion de {title} depende del numero de jugadores y experiencia del grupo.",
        },
        {
            "question": f"Para que tipo de jugadores es {title}?",
            "answer": f"{title} es ideal para coleccionistas, casuales y competitivos.",
        },
    ]

    if legacy_flat:
        return [f"{item['question']} {item['answer']}" for item in faq]

    return faq


def generate_faq_schema(listing: dict[str, Any]) -> dict[str, Any]:
    """
    Generates FAQ schema for structured data.

    Args:
        listing (dict[str, Any]): Product listing data.

    Returns:
        dict[str, Any]: Schema.org FAQPage structure.
    """
    faq_items = generate_faq(listing)

    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item["answer"]
                }
            }
            for item in faq_items
        ]
    }
