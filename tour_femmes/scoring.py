from __future__ import annotations

from dataclasses import dataclass

from tour_femmes.models import NON_FINISH_STATUSES

POINTS_BY_RANK = {
    1: 100,
    2: 85,
    3: 75,
    4: 65,
    5: 57,
    6: 50,
    7: 44,
    8: 38,
    9: 32,
    10: 26,
    11: 22,
    12: 18,
    13: 14,
    14: 10,
    15: 8,
    16: 6,
    17: 4,
    18: 2,
}
CAPTAIN_MULTIPLIER = 2
STAGE_WINNER_TEAMMATE_POINTS = 10
CLASSIFICATION_LABELS = {
    "gc": "Algemeen klassement (geel)",
    "points": "Puntenklassement (groen)",
    "mountains": "Bergklassement",
    "youth": "Jongerenklassement",
}
DAILY_CLASSIFICATION_POINTS = {
    "gc": (16, 10, 8, 6, 4),
    "points": (10, 6, 4, 2, 1),
    "mountains": (8, 6, 4, 2, 1),
    "youth": (5, 4, 3, 2, 1),
}
DAILY_LEADER_TEAMMATE_POINTS = {
    "gc": 14,
    "points": 8,
    "mountains": 6,
    "youth": 4,
}
FINAL_CLASSIFICATION_POINTS = {
    "gc": (200, 160, 130, 110, 90, 75, 60, 45, 30, 20),
    "points": (120, 90, 70, 55, 42, 34, 26, 20, 14, 8),
    "mountains": (100, 75, 55, 40, 30, 20, 14, 10, 6, 2),
    "youth": (70, 50, 35, 28, 22, 18, 14, 10, 6, 2),
}
FINAL_WINNER_TEAMMATE_POINTS = {
    "gc": 40,
    "points": 28,
    "mountains": 14,
    "youth": 14,
}


@dataclass(frozen=True)
class ScoringRule:
    rank: int
    points: int


@dataclass(frozen=True)
class RiderScore:
    event_rider_id: int
    base_points: int
    is_captain: bool
    rank: int | None = None
    status: str | None = None

    @property
    def total_points(self) -> int:
        return self.base_points * CAPTAIN_MULTIPLIER if self.is_captain else self.base_points

    @property
    def captain_bonus(self) -> int:
        return self.base_points if self.is_captain else 0


def points_for_result(rank: int | None, status: str | None) -> int:
    status = (status or "FIN").upper()
    if status in NON_FINISH_STATUSES or not rank:
        return 0
    return POINTS_BY_RANK.get(rank, 0)


def scoring_rules() -> list[ScoringRule]:
    return [ScoringRule(rank=rank, points=points) for rank, points in sorted(POINTS_BY_RANK.items())]


def classification_points(classification: str, rank: int, final: bool = False) -> int:
    table = FINAL_CLASSIFICATION_POINTS if final else DAILY_CLASSIFICATION_POINTS
    values = table.get(classification, ())
    return values[rank - 1] if 1 <= rank <= len(values) else 0


def score_lineup(
    lineup_event_rider_ids: set[int],
    captain_event_rider_id: int,
    result_points: dict[int, int],
) -> tuple[int, int, list[RiderScore]]:
    rider_scores = [
        RiderScore(
            event_rider_id=event_rider_id,
            base_points=result_points.get(event_rider_id, 0),
            is_captain=event_rider_id == captain_event_rider_id,
        )
        for event_rider_id in lineup_event_rider_ids
    ]
    total = sum(score.total_points for score in rider_scores)
    captain_bonus = sum(score.captain_bonus for score in rider_scores)
    return total, captain_bonus, rider_scores


def score_lineup_from_results(
    lineup_event_rider_ids: set[int],
    captain_event_rider_id: int,
    stage_results: dict[int, object],
) -> tuple[int, int, list[RiderScore]]:
    rider_scores: list[RiderScore] = []
    for event_rider_id in lineup_event_rider_ids:
        result = stage_results.get(event_rider_id)
        rank = getattr(result, "rank", None)
        status = getattr(result, "status", None)
        rider_scores.append(
            RiderScore(
                event_rider_id=event_rider_id,
                base_points=points_for_result(rank, status),
                is_captain=event_rider_id == captain_event_rider_id,
                rank=rank,
                status=status,
            )
        )
    rider_scores.sort(key=lambda score: (-score.total_points, score.event_rider_id))
    total = sum(score.total_points for score in rider_scores)
    captain_bonus = sum(score.captain_bonus for score in rider_scores)
    return total, captain_bonus, rider_scores
