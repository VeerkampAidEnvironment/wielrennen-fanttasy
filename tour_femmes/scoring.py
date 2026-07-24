from __future__ import annotations

from dataclasses import dataclass

from tour_femmes.models import NON_FINISH_STATUSES

POINTS_BY_RANK = {
    1: 100,
    2: 80,
    3: 65,
    4: 55,
    5: 45,
    6: 38,
    7: 32,
    8: 26,
    9: 21,
    10: 16,
    11: 12,
    12: 10,
    13: 8,
    14: 6,
    15: 4,
    16: 3,
    17: 2,
    18: 1,
}
CAPTAIN_MULTIPLIER = 2


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
