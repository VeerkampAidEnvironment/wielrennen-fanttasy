from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from tour_femmes.models import Event, Rider

SPORZA_EDITION_BY_PCS_RACE: dict[tuple[str, int], str] = {
    ("tour-de-france-femmes", 2026): "tour-v-26",
}

PRICE_FILE_BY_SPORZA_EDITION: dict[str, str] = {
    "tour-v-26": "tour-v-26-rider-prices.json",
}

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "sporza"


@dataclass(frozen=True)
class SporzaPriceCatalog:
    edition_slug: str
    prices_by_name: dict[str, int]

    def price_for_rider(self, rider: Rider) -> int | None:
        for candidate in rider_name_candidates(rider):
            price = self.prices_by_name.get(candidate)
            if price is not None:
                return price
        return None


def load_sporza_price_catalog(edition_slug: str) -> SporzaPriceCatalog:
    filename = PRICE_FILE_BY_SPORZA_EDITION.get(edition_slug)
    if not filename:
        return SporzaPriceCatalog(edition_slug=edition_slug, prices_by_name={})
    data = json.loads((DATA_DIR / filename).read_text(encoding="utf-8-sig"))
    return parse_sporza_price_catalog(edition_slug, data)


def parse_sporza_price_catalog(edition_slug: str, data: object) -> SporzaPriceCatalog:
    prices: dict[str, int] = {}
    cyclists = data.get("cyclists") if isinstance(data, dict) else data
    if not isinstance(cyclists, list):
        return SporzaPriceCatalog(edition_slug=edition_slug, prices_by_name=prices)

    for cyclist in cyclists:
        if not isinstance(cyclist, dict):
            continue
        price = cyclist.get("price")
        if not isinstance(price, int):
            continue
        names = [
            cyclist.get("fullName"),
            cyclist.get("sanitizedFullName"),
            " ".join(
                part
                for part in [str(cyclist.get("firstName") or ""), str(cyclist.get("lastName") or "")]
                if part
            ),
        ]
        for name in names:
            if isinstance(name, str) and name.strip():
                prices[normalize_rider_name(name)] = price

    return SporzaPriceCatalog(edition_slug=edition_slug, prices_by_name=prices)


def sporza_edition_for_event(event: Event) -> str | None:
    race_slug = pcs_race_slug(event.pcs_url) or event.slug
    return SPORZA_EDITION_BY_PCS_RACE.get((race_slug, event.year))


def pcs_race_slug(pcs_url: str) -> str | None:
    path_parts = [part for part in urlparse(pcs_url).path.split("/") if part]
    if len(path_parts) >= 2 and path_parts[0] == "race":
        return path_parts[1]
    return None


def rider_name_candidates(rider: Rider) -> list[str]:
    candidates = [rider.name]
    normalized_name = normalize_rider_name(rider.name)
    parts = normalized_name.split()
    if len(parts) >= 3:
        candidates.append(" ".join(parts[:-1]))
    if rider.pcs_slug:
        candidates.append(rider.pcs_slug.replace("-", " "))
        slug_parts = rider.pcs_slug.split("-")
        if len(slug_parts) >= 3:
            candidates.append(" ".join(slug_parts[:-1]))
    return list(dict.fromkeys(normalize_rider_name(candidate) for candidate in candidates if candidate))


def normalize_rider_name(value: str) -> str:
    without_accents = "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )
    lowered = without_accents.lower().replace("\u00df", "ss")
    return re.sub(r"[^a-z0-9]+", " ", lowered).strip()
