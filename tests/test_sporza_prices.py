from tour_femmes.models import Rider
from tour_femmes.services.sporza_prices import (
    load_sporza_price_catalog,
    normalize_rider_name,
    parse_sporza_price_catalog,
)


def test_parse_sporza_price_catalog_matches_accents_and_sanitized_names():
    catalog = parse_sporza_price_catalog(
        "tour-v-26",
        {
            "cyclists": [
                {
                    "firstName": "Pauline",
                    "lastName": "Ferrand-Prévot",
                    "fullName": "Pauline Ferrand-Prévot",
                    "sanitizedFullName": "Pauline Ferrand-Prevot",
                    "price": 10,
                }
            ]
        },
    )
    rider = Rider(
        pcs_slug="pauline-ferrand-prevot",
        pcs_url="https://www.procyclingstats.com/rider/pauline-ferrand-prevot",
        name="Pauline Ferrand-Prevot",
    )

    assert catalog.price_for_rider(rider) == 10


def test_normalize_rider_name_removes_punctuation_and_accents():
    assert normalize_rider_name("Fem van Empel") == "fem van empel"
    assert normalize_rider_name("Évita Muzic") == "evita muzic"


def test_static_tour_femmes_catalog_contains_known_prices():
    catalog = load_sporza_price_catalog("tour-v-26")
    rider = Rider(
        pcs_slug="demi-vollering",
        pcs_url="https://www.procyclingstats.com/rider/demi-vollering",
        name="Demi Vollering",
    )

    assert catalog.price_for_rider(rider) == 11


def test_catalog_matches_shorter_sporza_name_for_hyphenated_suffix():
    catalog = parse_sporza_price_catalog(
        "tour-v-26",
        [{"fullName": "Kim Le Court", "price": 7}],
    )
    rider = Rider(
        pcs_slug="kim-le-court-pienaar",
        pcs_url="https://www.procyclingstats.com/rider/kim-le-court-pienaar",
        name="Kim Le Court-Pienaar",
    )

    assert catalog.price_for_rider(rider) == 7
