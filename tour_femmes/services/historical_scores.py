from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

SCORE_CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "tdff_historical_scores.json"


@lru_cache(maxsize=1)
def load_historical_score_catalog() -> dict[str, list[dict[str, Any]]]:
    with SCORE_CATALOG_PATH.open(encoding="utf-8") as source:
        return json.load(source)["riders"]


@lru_cache(maxsize=512)
def historical_scores_for_rider_name(
    rider_name: str,
    pcs_slug: str = "",
) -> tuple[dict[str, Any], ...]:
    catalog = load_historical_score_catalog()
    candidates, surname_tokens = rider_name_candidates(rider_name, pcs_slug)

    for candidate in candidates:
        if candidate in catalog:
            return tuple(catalog[candidate])

    for candidate in candidates:
        if len(candidate.split()) < 2:
            continue
        matches = [
            key
            for key in catalog
            if key.startswith(f"{candidate} ") or candidate.startswith(f"{key} ")
        ]
        if len(matches) == 1:
            return tuple(catalog[matches[0]])

    if surname_tokens:
        slug_key = normalize_rider_name(pcs_slug)
        if not surname_tokens.intersection(slug_key.split()):
            return ()

    return ()


def historical_scores_for_rider(rider) -> tuple[dict[str, Any], ...]:
    return historical_scores_for_rider_name(rider.name, rider.pcs_slug)


def rider_name_candidates(rider_name: str, pcs_slug: str = "") -> tuple[list[str], set[str]]:
    candidates = [normalize_rider_name(rider_name)]
    parts = rider_name.split()
    surname_parts: list[str] = []
    given_name_index = next(
        (index for index, part in enumerate(parts) if not is_uppercase_name_part(part)),
        None,
    )
    if given_name_index:
        surname_parts = parts[:given_name_index]
        candidates.append(
            normalize_rider_name(" ".join(parts[given_name_index:] + surname_parts))
        )

    slug_key = normalize_rider_name(pcs_slug)
    surname_tokens = set(normalize_rider_name(" ".join(surname_parts)).split())
    if slug_key and (not surname_tokens or surname_tokens.intersection(slug_key.split())):
        candidates.append(slug_key)

    return list(dict.fromkeys(candidate for candidate in candidates if candidate)), surname_tokens


def normalize_rider_name(value: str) -> str:
    ascii_value = "".join(
        character
        for character in unicodedata.normalize("NFKD", value or "")
        if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", ascii_value.lower())).strip()


def is_uppercase_name_part(value: str) -> bool:
    letters = [character for character in value if character.isalpha()]
    return bool(letters) and all(character.isupper() for character in letters)
