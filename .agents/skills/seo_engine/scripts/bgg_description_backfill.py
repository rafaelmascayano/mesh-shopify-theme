import argparse
import html
import json
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any

BGG_SEARCH_URL = "https://boardgamegeek.com/xmlapi2/search"
BGG_THING_URL = "https://boardgamegeek.com/xmlapi2/thing"
GOOGLE_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"


@dataclass
class ListingCandidate:
    id: int
    title: str
    description: str


def get_supabase():
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise RuntimeError(
            "python-dotenv is required to read Supabase environment variables"
        ) from exc
    try:
        from supabase import create_client
    except ImportError as exc:
        raise RuntimeError("supabase package is required for DB updates") from exc

    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)


def fetch_listings(limit: int, listing_id: int | None = None) -> list[ListingCandidate]:
    query = get_supabase().table("listings").select("id,title,description")
    if listing_id is not None:
        response = query.eq("id", listing_id).limit(1).execute()
    else:
        response = query.limit(limit).execute()

    results = []
    for row in response.data or []:
        if not row.get("id") or not row.get("title"):
            continue
        results.append(
            ListingCandidate(
                id=int(row["id"]),
                title=str(row.get("title") or "").strip(),
                description=str(row.get("description") or "").strip(),
            )
        )
    return results


def is_poor_description(text: str) -> bool:
    if not text:
        return True

    normalized = re.sub(r"\s+", " ", text).strip().lower()
    words = re.findall(r"[a-záéíóúñ0-9]+", normalized, flags=re.IGNORECASE)
    unique_ratio = (len(set(words)) / len(words)) if words else 0

    low_signal_patterns = [
        "sin descripcion",
        "sin descripción",
        "muy buen estado",
        "consulta por interno",
        "precio conversable",
        "juego de mesa",
    ]

    if len(normalized) < 180:
        return True
    if unique_ratio < 0.42:
        return True
    return any(pattern in normalized for pattern in low_signal_patterns)


def _http_get(url: str, params: dict[str, Any], timeout: int = 20) -> str:
    query = urllib.parse.urlencode(params, doseq=True)
    full_url = f"{url}?{query}"
    request = urllib.request.Request(
        full_url, headers={"User-Agent": "tablerodevuelta-seo-bot/1.0"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def search_bgg_game_id(title: str) -> str | None:
    xml_data = _http_get(BGG_SEARCH_URL, {"query": title, "type": "boardgame"})
    root = ET.fromstring(xml_data)
    items = root.findall("item")
    if not items:
        return None

    title_norm = normalize_title(title)
    best_id = None
    best_score = -1
    for item in items[:8]:
        item_id = item.attrib.get("id")
        primary_name = item.find("name[@type='primary']")
        candidate_name = primary_name.attrib.get("value", "") if primary_name is not None else ""
        score = similarity_score(title_norm, normalize_title(candidate_name))
        if score > best_score:
            best_score = score
            best_id = item_id

    return best_id


def fetch_bgg_description(game_id: str, max_retries: int = 6, wait_seconds: int = 2) -> str | None:
    for _ in range(max_retries):
        request = urllib.request.Request(
            f"{BGG_THING_URL}?{urllib.parse.urlencode({'id': game_id})}",
            headers={"User-Agent": "tablerodevuelta-seo-bot/1.0"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            status = getattr(response, "status", 200)
            if status == 202:
                time.sleep(wait_seconds)
                continue
            xml_data = response.read().decode("utf-8", errors="ignore")

        root = ET.fromstring(xml_data)
        item = root.find("item")
        if item is None:
            return None
        desc_node = item.find("description")
        if desc_node is None or not desc_node.text:
            return None
        return clean_bgg_text(desc_node.text)

    return None


def clean_bgg_text(raw_text: str) -> str:
    text = html.unescape(raw_text)
    text = re.sub(r"\[/?[a-z]+(?:=[^\]]+)?\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"([.!?])\s+", r"\1\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def translate_to_spanish(text: str, source_lang: str = "auto") -> str | None:
    if not text:
        return None

    chunks = split_text(text, 3000)
    translated_chunks = []
    for chunk in chunks:
        payload = {
            "client": "gtx",
            "sl": source_lang,
            "tl": "es",
            "dt": "t",
            "q": chunk,
        }
        raw = _http_get(GOOGLE_TRANSLATE_URL, payload)
        try:
            data = json.loads(raw)
            piece = "".join(segment[0] for segment in data[0] if segment and segment[0])
        except Exception:
            return None
        translated_chunks.append(piece)
    return "\n\n".join(part.strip() for part in translated_chunks if part.strip()).strip()


def split_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        candidate = f"{current} {sentence}".strip()
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = sentence
    if current:
        chunks.append(current)
    return chunks


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def similarity_score(a: str, b: str) -> int:
    if not a or not b:
        return 0
    if a == b:
        return 100
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    if not tokens_a or not tokens_b:
        return 0
    overlap = len(tokens_a & tokens_b)
    return int(100 * overlap / max(len(tokens_a), len(tokens_b)))


def update_listing_description(listing_id: int, description: str) -> None:
    get_supabase().table("listings").update({"description": description}).eq(
        "id", listing_id
    ).execute()


def process_candidates(
    candidates: list[ListingCandidate], apply_updates: bool, source_lang: str
) -> list[dict[str, Any]]:
    report: list[dict[str, Any]] = []

    for candidate in candidates:
        item_report: dict[str, Any] = {
            "id": candidate.id,
            "title": candidate.title,
            "status": "skipped",
            "reason": "",
        }

        if not is_poor_description(candidate.description):
            item_report["reason"] = "description-good-enough"
            report.append(item_report)
            continue

        game_id = search_bgg_game_id(candidate.title)
        if not game_id:
            item_report["reason"] = "bgg-not-found"
            report.append(item_report)
            continue

        bgg_description = fetch_bgg_description(game_id)
        if not bgg_description or len(bgg_description) < 120:
            item_report["reason"] = "bgg-description-too-short"
            report.append(item_report)
            continue

        translated = translate_to_spanish(bgg_description, source_lang=source_lang)
        if not translated:
            item_report["reason"] = "translation-failed"
            report.append(item_report)
            continue

        if apply_updates:
            update_listing_description(candidate.id, translated)
            item_report["status"] = "updated"
            item_report["reason"] = "applied"
        else:
            item_report["status"] = "ready"
            item_report["reason"] = "dry-run"

        item_report["preview"] = translated[:240]
        report.append(item_report)
        time.sleep(1)

    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill poor listing descriptions from BGG and translate to Spanish."
    )
    parser.add_argument("--limit", type=int, default=100, help="Max listings to evaluate.")
    parser.add_argument("--listing-id", type=int, default=None, help="Process a single listing id.")
    parser.add_argument(
        "--source-lang",
        default="auto",
        help="Source language hint for translation. Default: auto",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist updates into Supabase. Default is dry-run.",
    )
    parser.add_argument(
        "--report-file",
        default=None,
        help="Optional file path to save JSON report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    candidates = fetch_listings(limit=args.limit, listing_id=args.listing_id)
    report = process_candidates(
        candidates=candidates,
        apply_updates=args.apply,
        source_lang=args.source_lang,
    )

    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)

    if args.report_file:
        with open(args.report_file, "w", encoding="utf-8") as handle:
            handle.write(output)


if __name__ == "__main__":
    main()
