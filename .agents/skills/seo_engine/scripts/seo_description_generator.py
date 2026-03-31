from typing import Any


def _normalize_title(raw_title: Any) -> str:
    title = str(raw_title or "").strip()
    return title or "Este juego de mesa"


def _players_phrase(players_min: Any, players_max: Any) -> str:
    try:
        pmin = int(players_min) if players_min is not None else None
        pmax = int(players_max) if players_max is not None else None
    except (TypeError, ValueError):
        return "distintos numeros de jugadores"

    if pmin and pmax and pmin > 0 and pmax > 0:
        if pmin == pmax:
            return f"{pmin} jugador{'es' if pmin != 1 else ''}"
        return f"{pmin} a {pmax} jugadores"
    if pmin and pmin > 0:
        return f"{pmin} o mas jugadores"
    if pmax and pmax > 0:
        return f"hasta {pmax} jugadores"
    return "distintos numeros de jugadores"


def generate_seo_description(listing: dict[str, Any]) -> str:
    """
    Generates an optimized description for product pages containing
    a product overview, gameplay description, player count, and ideal audience.

    Args:
        listing (dict[str, Any]): The product listing containing 'title', 'players_min', 'players_max'.

    Returns:
        str: A multi-paragraph SEO description string.
    """
    title = _normalize_title(listing.get("title"))
    players = _players_phrase(listing.get("players_min"), listing.get("players_max"))

    paragraphs = [
        f"{title} es un juego de mesa pensado para {players}.",
        "Entrega una experiencia entretenida con decisiones tacticas y buena rejugabilidad.",
        (
            "Es una alternativa ideal para compartir con familia o amigos, "
            "tanto en partidas casuales como en mesas mas competitivas."
        ),
        (
            "Si estas buscando un titulo versatil para tu coleccion, "
            f"{title} destaca por su dinamica, interaccion y valor de repeticion."
        ),
    ]

    return "\n\n".join(paragraphs)
