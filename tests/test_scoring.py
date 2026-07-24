from tour_femmes.scoring import points_for_result, score_lineup


def test_points_for_ranked_finisher():
    assert points_for_result(1, "FIN") == 100
    assert points_for_result(18, "FIN") == 1
    assert points_for_result(30, "FIN") == 0


def test_non_finish_statuses_score_zero():
    assert points_for_result(1, "DNF") == 0
    assert points_for_result(None, "FIN") == 0


def test_captain_doubles_only_their_points():
    total, captain_bonus, rider_scores = score_lineup(
        {10, 20, 30},
        20,
        {10: 100, 20: 80, 30: 65},
    )

    assert total == 325
    assert captain_bonus == 80
    assert [score.total_points for score in rider_scores] == [100, 160, 65]
