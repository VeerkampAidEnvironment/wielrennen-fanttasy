from types import SimpleNamespace

from tour_femmes.services.historical_scores import historical_scores_for_rider


def test_historical_scores_match_pcs_surname_first_name():
    rider = SimpleNamespace(name="VOS Marianne", pcs_slug="marianne-vos")

    scores = historical_scores_for_rider(rider)

    assert [score["year"] for score in scores] == [2025, 2024, 2023, 2022]
    assert scores[-1]["rank"] == 1
    assert scores[-1]["points"] == 754


def test_historical_scores_match_unique_longer_catalog_name():
    rider = SimpleNamespace(name="NIEWIADOMA Kasia", pcs_slug="katarzyna-niewiadoma")

    scores = historical_scores_for_rider(rider)

    assert scores[0]["year"] == 2025
    assert scores[0]["points"] == 548


def test_historical_scores_reject_inconsistent_slug():
    rider = SimpleNamespace(name="BERTHET Juliette", pcs_slug="juliette-labous")

    assert historical_scores_for_rider(rider) == ()
