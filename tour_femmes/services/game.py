from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import selectinload

from tour_femmes import db
from tour_femmes.models import (
    Award,
    ClassificationResult,
    Event,
    EventEntry,
    EventRider,
    Stage,
    StageLineup,
    StageLineupRider,
    StageResult,
    TeamSelection,
    TeamSelectionRider,
    User,
    UserStageRiderScore,
    UserStageScore,
    utcnow,
)
from tour_femmes.scoring import (
    DAILY_LEADER_TEAMMATE_POINTS,
    FINAL_WINNER_TEAMMATE_POINTS,
    STAGE_WINNER_TEAMMATE_POINTS,
    classification_points,
    points_for_result,
    score_lineup_from_results,
)


@dataclass(frozen=True)
class SelectionValidation:
    ok: bool
    message: str
    selected_riders: list[EventRider]
    total_price: int


@dataclass(frozen=True)
class SelectionProgress:
    state: str
    count: int
    required: int
    label: str


@dataclass(frozen=True)
class RiderSelectionPopularity:
    event_rider: EventRider
    selected_count: int
    percentage: int


@dataclass(frozen=True)
class ParticipantTeamOverview:
    user: User
    riders: tuple[EventRider, ...]
    total_price: int
    complete: bool


@dataclass(frozen=True)
class TeamSelectionOverview:
    participant_count: int
    selection_count: int
    completed_count: int
    unique_rider_count: int
    average_total_price: float
    popularity: tuple[RiderSelectionPopularity, ...]
    participant_teams: tuple[ParticipantTeamOverview, ...]


@dataclass(frozen=True)
class LeaderboardRow:
    user: User
    total_score: int
    latest_stage_score: int
    stage_scores: dict[int, int]
    stage_wins: int
    stage_win_numbers: frozenset[int]
    yellow_stage_numbers: frozenset[int]
    is_yellow: bool


@dataclass(frozen=True)
class StageLineupRiderView:
    event_rider: EventRider
    is_captain: bool
    points: int
    rank_label: str


@dataclass(frozen=True)
class StageLeaderboardRow:
    user: User
    score: int
    has_score: bool
    captain_bonus: int
    lineup_riders: tuple[StageLineupRiderView, ...]
    is_stage_winner: bool
    is_yellow_after_stage: bool


@dataclass(frozen=True)
class RiderStageHistoryItem:
    stage_number: int
    stage_name: str
    rank_label: str
    points: int


@dataclass(frozen=True)
class RiderStageHistory:
    event_rider_id: int
    total_points: int
    results: list[RiderStageHistoryItem]


@dataclass(frozen=True)
class OfficialRiderStageScore:
    event_rider_id: int
    stage_points: int
    classification_points: int
    teammate_points: int
    total_points: int


def get_or_create_entry(user: User, event: Event) -> EventEntry:
    entry = EventEntry.query.filter_by(user_id=user.id, event_id=event.id).first()
    if entry:
        return entry
    entry = EventEntry(user=user, event=event)
    db.session.add(entry)
    return entry


def get_team_selection(user: User, event: Event) -> TeamSelection | None:
    return TeamSelection.query.filter_by(user_id=user.id, event_id=event.id).first()


def validate_team_selection(event: Event, rider_ids: list[int], require_exact: bool = True) -> SelectionValidation:
    try:
        unique_ids = sorted({int(rider_id) for rider_id in rider_ids})
    except ValueError:
        return SelectionValidation(False, "Een of meer gekozen renners zijn ongeldig.", [], 0)

    selected = (
        EventRider.query.filter(
            EventRider.event_id == event.id,
            EventRider.id.in_(unique_ids) if unique_ids else False,
        )
        .order_by(EventRider.id)
        .all()
    )

    if require_exact and len(unique_ids) != event.team_size:
        return SelectionValidation(
            False,
            f"Kies precies {event.team_size} renners.",
            selected,
            sum(rider.price or 0 for rider in selected),
        )
    if not require_exact and len(unique_ids) > event.team_size:
        return SelectionValidation(
            False,
            f"Kies maximaal {event.team_size} renners.",
            selected,
            sum(rider.price or 0 for rider in selected),
        )

    if len(selected) != len(unique_ids) or any(not rider.selectable for rider in selected):
        return SelectionValidation(False, "Een of meer gekozen renners zijn niet beschikbaar.", selected, 0)

    total = sum(rider.price or 0 for rider in selected)
    if total > event.budget:
        return SelectionValidation(False, f"Budget overschreden: {total} / {event.budget}.", selected, total)

    if len(unique_ids) == event.team_size:
        return SelectionValidation(True, "Teamselectie opgeslagen.", selected, total)
    return SelectionValidation(True, f"Concept opgeslagen: {len(unique_ids)} / {event.team_size} renners.", selected, total)


def save_team_selection(user: User, event: Event, selected_riders: list[EventRider], total_price: int) -> TeamSelection:
    get_or_create_entry(user, event)
    selection = get_team_selection(user, event)
    if not selection:
        selection = TeamSelection(user=user, event=event)
        db.session.add(selection)

    selection.submitted_at = utcnow()
    selection.total_price = total_price
    selection.riders.clear()
    db.session.flush()
    for event_rider in selected_riders:
        selection.riders.append(TeamSelectionRider(event_rider=event_rider))
    return selection


def lineup_status(user: User, stage: Stage) -> str:
    if stage.is_finished or stage.has_ranked_result():
        return "Afgelopen"
    if stage.is_locked():
        return "Bezig"
    lineup = StageLineup.query.filter_by(user_id=user.id, stage_id=stage.id).first()
    if not lineup:
        return "Ontbreekt"
    if len(lineup.riders) != stage.event.lineup_size:
        return "Niet compleet"
    return "Compleet"


def event_selection_progress(
    user: User,
    event: Event,
) -> dict[str | int, SelectionProgress]:
    selection = (
        TeamSelection.query.options(selectinload(TeamSelection.riders))
        .filter_by(user_id=user.id, event_id=event.id)
        .first()
    )
    selected_count = len(selection.riders) if selection else 0
    team_complete = bool(
        selection
        and selected_count == event.team_size
        and selection.total_price <= event.budget
    )
    progress: dict[str | int, SelectionProgress] = {
        "team": _selection_progress(selected_count, event.team_size, team_complete)
    }

    stage_ids = [stage.id for stage in event.stages]
    lineups = (
        StageLineup.query.options(selectinload(StageLineup.riders))
        .filter(
            StageLineup.user_id == user.id,
            StageLineup.stage_id.in_(stage_ids),
        )
        .all()
        if stage_ids
        else []
    )
    lineup_by_stage_id = {lineup.stage_id: lineup for lineup in lineups}
    for stage in event.stages:
        lineup = lineup_by_stage_id.get(stage.id)
        rider_ids = lineup.rider_ids() if lineup else set()
        if stage.is_finished or stage.has_ranked_result():
            progress[stage.id] = SelectionProgress(
                "finished",
                len(rider_ids),
                event.lineup_size,
                "Afgelopen",
            )
            continue
        if stage.is_locked():
            progress[stage.id] = SelectionProgress(
                "ongoing",
                len(rider_ids),
                event.lineup_size,
                "Bezig",
            )
            continue
        lineup_complete = bool(
            lineup
            and len(rider_ids) == event.lineup_size
            and lineup.captain_event_rider_id in rider_ids
        )
        progress[stage.id] = _selection_progress(
            len(rider_ids),
            event.lineup_size,
            lineup_complete,
        )
    return progress


def build_team_selection_overview(event: Event) -> TeamSelectionOverview:
    entries = (
        EventEntry.query.options(selectinload(EventEntry.user))
        .filter_by(event_id=event.id, status="active")
        .all()
    )
    entries.sort(key=lambda entry: entry.user.username.casefold())

    selections = (
        TeamSelection.query.options(
            selectinload(TeamSelection.riders)
            .joinedload(TeamSelectionRider.event_rider)
            .joinedload(EventRider.rider),
            selectinload(TeamSelection.riders)
            .joinedload(TeamSelectionRider.event_rider)
            .joinedload(EventRider.team),
        )
        .filter_by(event_id=event.id)
        .all()
    )
    selection_by_user_id = {selection.user_id: selection for selection in selections}
    selected_counts: dict[int, int] = defaultdict(int)
    selected_riders: dict[int, EventRider] = {}
    participant_teams: list[ParticipantTeamOverview] = []
    totals_with_riders: list[int] = []

    for entry in entries:
        selection = selection_by_user_id.get(entry.user_id)
        riders = tuple(
            sorted(
                (link.event_rider for link in selection.riders) if selection else (),
                key=lambda event_rider: (
                    -(event_rider.price or 0),
                    event_rider.rider.name.casefold(),
                ),
            )
        )
        total_price = selection.total_price if selection else 0
        complete = bool(
            selection
            and len(riders) == event.team_size
            and total_price <= event.budget
        )
        if riders:
            totals_with_riders.append(total_price)
        for event_rider in riders:
            selected_counts[event_rider.id] += 1
            selected_riders[event_rider.id] = event_rider
        participant_teams.append(
            ParticipantTeamOverview(
                user=entry.user,
                riders=riders,
                total_price=total_price,
                complete=complete,
            )
        )

    participant_count = len(entries)
    popularity = tuple(
        RiderSelectionPopularity(
            event_rider=selected_riders[event_rider_id],
            selected_count=selected_count,
            percentage=(
                round((selected_count / participant_count) * 100)
                if participant_count
                else 0
            ),
        )
        for event_rider_id, selected_count in sorted(
            selected_counts.items(),
            key=lambda item: (
                -item[1],
                -(selected_riders[item[0]].price or 0),
                selected_riders[item[0]].rider.name.casefold(),
            ),
        )
    )
    return TeamSelectionOverview(
        participant_count=participant_count,
        selection_count=sum(bool(team.riders) for team in participant_teams),
        completed_count=sum(team.complete for team in participant_teams),
        unique_rider_count=len(selected_counts),
        average_total_price=(
            round(sum(totals_with_riders) / len(totals_with_riders), 1)
            if totals_with_riders
            else 0
        ),
        popularity=popularity,
        participant_teams=tuple(participant_teams),
    )


def _selection_progress(
    count: int,
    required: int,
    complete: bool,
) -> SelectionProgress:
    if complete:
        return SelectionProgress("complete", count, required, "Compleet")
    if count:
        return SelectionProgress("partial", count, required, f"{count}/{required}")
    return SelectionProgress("empty", 0, required, "Leeg")


def save_stage_lineup(
    user: User,
    stage: Stage,
    rider_ids: list[int | str],
    captain_id: int,
    require_exact: bool = True,
) -> tuple[bool, str]:
    event = stage.event
    selection = get_team_selection(user, event)
    if not selection or len(selection.riders) != event.team_size:
        return False, "Maak eerst je teamselectie compleet."

    try:
        unique_ids = sorted({int(rider_id) for rider_id in rider_ids})
    except (TypeError, ValueError):
        return False, "Een of meer gekozen renners zijn ongeldig."

    selection_ids = selection.rider_ids()
    if require_exact and len(unique_ids) != event.lineup_size:
        return False, f"Kies precies {event.lineup_size} renners voor deze etappe."
    if not require_exact and len(unique_ids) > event.lineup_size:
        return False, f"Kies maximaal {event.lineup_size} renners voor deze etappe."
    if not set(unique_ids).issubset(selection_ids):
        return False, "Etapperenners moeten uit je koersselectie komen."

    lineup = StageLineup.query.filter_by(user_id=user.id, stage_id=stage.id).first()
    if not unique_ids:
        if lineup:
            db.session.delete(lineup)
        return True, f"Concept opgeslagen: 0 / {event.lineup_size} renners."

    if captain_id not in unique_ids:
        if require_exact:
            return False, "De kopvrouw moet in je etappeselectie zitten."
        captain_id = unique_ids[0]

    if not lineup:
        lineup = StageLineup(user=user, stage=stage, captain_event_rider_id=captain_id)
        db.session.add(lineup)

    lineup.captain_event_rider_id = captain_id
    lineup.submitted_at = utcnow()
    lineup.riders.clear()
    db.session.flush()
    for event_rider_id in unique_ids:
        lineup.riders.append(StageLineupRider(event_rider_id=event_rider_id))
    if len(unique_ids) == event.lineup_size:
        return True, "Etappeselectie opgeslagen."
    return True, f"Concept opgeslagen: {len(unique_ids)} / {event.lineup_size} renners."


def recalculate_stage_scores(stage: Stage) -> None:
    results_by_rider = {result.event_rider_id: result for result in stage.results}
    for result in stage.results:
        result.base_points = points_for_result(result.rank, result.status)

    lineup_by_user = {lineup.user_id: lineup for lineup in stage.lineups}
    selections = TeamSelection.query.filter_by(event_id=stage.event_id).all()
    selection_by_user = {selection.user_id: selection for selection in selections}
    final_results_present = any(result.is_final for result in stage.classification_results)
    user_ids = set(lineup_by_user)
    if final_results_present:
        user_ids.update(selection_by_user)

    for user_id in user_ids:
        lineup = lineup_by_user.get(user_id)
        lineup_ids = lineup.rider_ids() if lineup else set()
        if len(lineup_ids) == stage.event.lineup_size and lineup.captain_event_rider_id in lineup_ids:
            total, captain_bonus, rider_scores = score_lineup_from_results(
                lineup_ids,
                lineup.captain_event_rider_id,
                results_by_rider,
            )
        else:
            total = 0
            captain_bonus = 0
            rider_scores = []
        selection = selection_by_user.get(user_id)
        final_eligible_ids = selection.rider_ids() if selection else set()
        bonuses = calculate_classification_bonuses(
            stage,
            daily_eligible_ids=lineup_ids,
            final_eligible_ids=final_eligible_ids,
        )
        total += sum(sum(parts) for parts in bonuses.values())

        score = UserStageScore.query.filter_by(user_id=user_id, stage_id=stage.id).first()
        if not score:
            score = UserStageScore(user_id=user_id, stage_id=stage.id)
            db.session.add(score)
        score.score = total
        score.captain_bonus = captain_bonus
        score.calculated_at = utcnow()
        score.rider_scores.clear()
        db.session.flush()
        rider_score_by_id = {item.event_rider_id: item for item in rider_scores}
        scored_rider_ids = set(rider_score_by_id) | {
            event_rider_id
            for event_rider_id, parts in bonuses.items()
            if any(parts)
        }
        for event_rider_id in scored_rider_ids:
            rider_score = rider_score_by_id.get(event_rider_id)
            daily_points, teammate_points, final_points, final_teammate_points = bonuses.get(
                event_rider_id,
                (0, 0, 0, 0),
            )
            base_points = rider_score.base_points if rider_score else 0
            rider_captain_bonus = rider_score.captain_bonus if rider_score else 0
            result = results_by_rider.get(event_rider_id)
            db.session.add(
                UserStageRiderScore(
                    score=score,
                    event_rider_id=event_rider_id,
                    rank=rider_score.rank if rider_score else None,
                    status=(rider_score.status if rider_score and result else "Klassementsbonus"),
                    base_points=base_points,
                    captain_bonus=rider_captain_bonus,
                    classification_points=daily_points,
                    teammate_points=teammate_points,
                    final_classification_points=final_points,
                    final_teammate_points=final_teammate_points,
                    total_points=(
                        base_points
                        + rider_captain_bonus
                        + daily_points
                        + teammate_points
                        + final_points
                        + final_teammate_points
                    ),
                )
            )

    stage.is_finished = stage.has_ranked_result()
    stage.results_imported_at = utcnow()
    recalculate_event_awards(stage.event)


def calculate_classification_bonuses(
    stage: Stage,
    daily_eligible_ids: set[int],
    final_eligible_ids: set[int],
) -> dict[int, tuple[int, int, int, int]]:
    """Return daily, daily-teammate, final and final-teammate points per rider."""
    values: dict[int, list[int]] = defaultdict(lambda: [0, 0, 0, 0])
    event_riders = {
        link.id: link
        for link in EventRider.query.filter_by(event_id=stage.event_id).all()
    }
    by_classification: dict[str, list[ClassificationResult]] = defaultdict(list)
    for result in stage.classification_results:
        by_classification[result.classification].append(result)

    for classification, results in by_classification.items():
        ordered = sorted(results, key=lambda result: result.rank)
        # The final standings are also the daily standings after the last stage.
        daily_results = ordered
        final_results = [result for result in ordered if result.is_final]

        for result in daily_results:
            if result.event_rider_id in daily_eligible_ids:
                values[result.event_rider_id][0] += classification_points(
                    classification,
                    result.rank,
                    final=False,
                )
        if daily_results:
            leader = daily_results[0]
            leader_team_id = event_riders[leader.event_rider_id].team_id
            for event_rider_id in daily_eligible_ids:
                link = event_riders.get(event_rider_id)
                if (
                    link
                    and leader_team_id
                    and link.team_id == leader_team_id
                    and event_rider_id != leader.event_rider_id
                ):
                    values[event_rider_id][1] += DAILY_LEADER_TEAMMATE_POINTS.get(classification, 0)

        for result in final_results:
            if result.event_rider_id in final_eligible_ids:
                values[result.event_rider_id][2] += classification_points(
                    classification,
                    result.rank,
                    final=True,
                )
        if final_results:
            winner = final_results[0]
            winner_team_id = event_riders[winner.event_rider_id].team_id
            for event_rider_id in final_eligible_ids:
                link = event_riders.get(event_rider_id)
                if (
                    link
                    and winner_team_id
                    and link.team_id == winner_team_id
                    and event_rider_id != winner.event_rider_id
                ):
                    values[event_rider_id][3] += FINAL_WINNER_TEAMMATE_POINTS.get(classification, 0)

    stage_winner = next(
        (
            result
            for result in stage.results
            if result.rank == 1 and result.status not in {"DNF", "DNS", "DSQ", "OTL", "DF", "NR"}
        ),
        None,
    )
    if stage_winner:
        winner_link = event_riders.get(stage_winner.event_rider_id)
        winner_team_id = winner_link.team_id if winner_link else None
        for event_rider_id in daily_eligible_ids:
            link = event_riders.get(event_rider_id)
            if (
                link
                and winner_team_id
                and link.team_id == winner_team_id
                and event_rider_id != stage_winner.event_rider_id
            ):
                values[event_rider_id][1] += STAGE_WINNER_TEAMMATE_POINTS

    return {event_rider_id: tuple(parts) for event_rider_id, parts in values.items()}


def build_official_stage_scores(stage: Stage) -> dict[int, OfficialRiderStageScore]:
    """Return neutral rider totals without user-specific captain bonuses."""
    event_rider_ids = {
        event_rider.id
        for event_rider in EventRider.query.filter_by(event_id=stage.event_id).all()
    }
    bonuses = calculate_classification_bonuses(
        stage,
        daily_eligible_ids=event_rider_ids,
        final_eligible_ids=event_rider_ids,
    )
    results_by_rider = {result.event_rider_id: result for result in stage.results}
    scored_rider_ids = set(results_by_rider) | set(bonuses)

    scores: dict[int, OfficialRiderStageScore] = {}
    for event_rider_id in scored_rider_ids:
        result = results_by_rider.get(event_rider_id)
        stage_points = points_for_result(result.rank, result.status) if result else 0
        daily, teammate, final, final_teammate = bonuses.get(
            event_rider_id,
            (0, 0, 0, 0),
        )
        classification_total = daily + final
        teammate_total = teammate + final_teammate
        scores[event_rider_id] = OfficialRiderStageScore(
            event_rider_id=event_rider_id,
            stage_points=stage_points,
            classification_points=classification_total,
            teammate_points=teammate_total,
            total_points=stage_points + classification_total + teammate_total,
        )
    return scores


def recalculate_event_awards(event: Event) -> None:
    Award.query.filter_by(event_id=event.id).delete()
    finished_stages = [stage for stage in event.stages if stage.has_ranked_result()]

    running_totals: dict[int, int] = defaultdict(int)
    for stage in finished_stages:
        scores = UserStageScore.query.filter_by(stage_id=stage.id).all()
        if scores:
            max_stage_score = max(score.score for score in scores)
            for score in scores:
                running_totals[score.user_id] += score.score
                if max_stage_score > 0 and score.score == max_stage_score:
                    db.session.add(
                        Award(
                            event_id=event.id,
                            stage_id=stage.id,
                            user_id=score.user_id,
                            award_type="stage_win",
                        )
                    )
        if running_totals:
            yellow_score = max(running_totals.values())
            for user_id, total in running_totals.items():
                if yellow_score > 0 and total == yellow_score:
                    db.session.add(
                        Award(
                            event_id=event.id,
                            stage_id=stage.id,
                            user_id=user_id,
                            award_type="yellow_jersey",
                        )
                    )


def build_leaderboard(
    event: Event,
    user_ids: set[int] | None = None,
) -> list[LeaderboardRow]:
    stages = list(event.stages)
    latest_stage = latest_finished_stage(event)
    scores_by_user: dict[int, dict[int, int]] = defaultdict(dict)
    totals = defaultdict(int)

    scores = (
        UserStageScore.query.join(Stage)
        .filter(Stage.event_id == event.id)
        .all()
    )
    for score in scores:
        scores_by_user[score.user_id][score.stage.number] = score.score
        totals[score.user_id] += score.score

    stage_win_numbers: dict[int, set[int]] = defaultdict(set)
    yellow_stage_numbers: dict[int, set[int]] = defaultdict(set)
    if user_ids is None:
        award_rows = (
            Award.query.join(Stage, Award.stage_id == Stage.id)
            .filter(
                Award.event_id == event.id,
                Award.award_type.in_(("stage_win", "yellow_jersey")),
            )
            .all()
        )
        for award in award_rows:
            if award.award_type == "stage_win":
                stage_win_numbers[award.user_id].add(award.stage.number)
            elif award.award_type == "yellow_jersey":
                yellow_stage_numbers[award.user_id].add(award.stage.number)
        yellow_user_ids = current_yellow_user_ids(event)
    else:
        stage_win_numbers, yellow_stage_numbers = _relative_awards(
            stages,
            scores_by_user,
            user_ids,
        )
        yellow_user_ids = {
            user_id
            for user_id, stage_numbers in yellow_stage_numbers.items()
            if latest_stage and latest_stage.number in stage_numbers
        }

    entry_query = EventEntry.query.filter_by(event_id=event.id, status="active")
    if user_ids is not None:
        entry_query = entry_query.filter(EventEntry.user_id.in_(user_ids))
    entries = entry_query.all()
    rows = []
    for entry in entries:
        latest_score = scores_by_user[entry.user_id].get(latest_stage.number, 0) if latest_stage else 0
        user_stage_wins = stage_win_numbers[entry.user_id]
        rows.append(
            LeaderboardRow(
                user=entry.user,
                total_score=totals[entry.user_id],
                latest_stage_score=latest_score,
                stage_scores={stage.number: scores_by_user[entry.user_id].get(stage.number, 0) for stage in stages},
                stage_wins=len(user_stage_wins),
                stage_win_numbers=frozenset(user_stage_wins),
                yellow_stage_numbers=frozenset(yellow_stage_numbers[entry.user_id]),
                is_yellow=entry.user_id in yellow_user_ids,
            )
        )
    rows.sort(key=lambda row: (-row.total_score, row.user.username.lower()))
    return rows


def build_stage_leaderboard(
    event: Event,
    stage: Stage,
    user_ids: set[int] | None = None,
) -> list[StageLeaderboardRow]:
    entry_query = EventEntry.query.filter_by(event_id=event.id, status="active")
    if user_ids is not None:
        entry_query = entry_query.filter(EventEntry.user_id.in_(user_ids))
    entries = entry_query.all()
    lineups = StageLineup.query.filter_by(stage_id=stage.id).all()
    scores = UserStageScore.query.filter_by(stage_id=stage.id).all()
    lineup_by_user = {lineup.user_id: lineup for lineup in lineups}
    score_by_user = {score.user_id: score for score in scores}

    if user_ids is None:
        awards = Award.query.filter_by(event_id=event.id, stage_id=stage.id).all()
        stage_winner_ids = {award.user_id for award in awards if award.award_type == "stage_win"}
        yellow_user_ids = {award.user_id for award in awards if award.award_type == "yellow_jersey"}
    else:
        total_rows = build_leaderboard(event, user_ids)
        stage_winner_ids = {
            row.user.id for row in total_rows if stage.number in row.stage_win_numbers
        }
        yellow_user_ids = {
            row.user.id for row in total_rows if stage.number in row.yellow_stage_numbers
        }

    rows = []
    for entry in entries:
        lineup = lineup_by_user.get(entry.user_id)
        score = score_by_user.get(entry.user_id)
        rider_score_by_id = {
            rider_score.event_rider_id: rider_score
            for rider_score in score.rider_scores
        } if score else {}
        lineup_riders = []
        if lineup:
            for link in lineup.riders:
                rider_score = rider_score_by_id.get(link.event_rider_id)
                rank_label = "Nog geen uitslag"
                points = 0
                if rider_score:
                    rank_label = f"#{rider_score.rank}" if rider_score.rank else (rider_score.status or "—")
                    points = rider_score.total_points
                lineup_riders.append(
                    StageLineupRiderView(
                        event_rider=link.event_rider,
                        is_captain=link.event_rider_id == lineup.captain_event_rider_id,
                        points=points,
                        rank_label=rank_label,
                    )
                )
        lineup_riders.sort(
            key=lambda rider: (
                not rider.is_captain,
                -rider.points,
                rider.event_rider.rider.name.lower(),
            )
        )
        rows.append(
            StageLeaderboardRow(
                user=entry.user,
                score=score.score if score else 0,
                has_score=score is not None,
                captain_bonus=score.captain_bonus if score else 0,
                lineup_riders=tuple(lineup_riders),
                is_stage_winner=entry.user_id in stage_winner_ids,
                is_yellow_after_stage=entry.user_id in yellow_user_ids,
            )
        )

    rows.sort(key=lambda row: (-row.score, row.user.username.lower()))
    return rows


def _relative_awards(
    stages: list[Stage],
    scores_by_user: dict[int, dict[int, int]],
    user_ids: set[int],
) -> tuple[dict[int, set[int]], dict[int, set[int]]]:
    stage_win_numbers: dict[int, set[int]] = defaultdict(set)
    yellow_stage_numbers: dict[int, set[int]] = defaultdict(set)
    running_totals: dict[int, int] = defaultdict(int)

    for stage in stages:
        if not stage.has_ranked_result():
            continue
        stage_scores = {
            user_id: scores_by_user[user_id][stage.number]
            for user_id in user_ids
            if stage.number in scores_by_user[user_id]
        }
        if stage_scores:
            winning_score = max(stage_scores.values())
            if winning_score > 0:
                for user_id, score in stage_scores.items():
                    if score == winning_score:
                        stage_win_numbers[user_id].add(stage.number)
            for user_id, score in stage_scores.items():
                running_totals[user_id] += score
        if running_totals:
            leading_score = max(running_totals.values())
            if leading_score > 0:
                for user_id, total in running_totals.items():
                    if total == leading_score:
                        yellow_stage_numbers[user_id].add(stage.number)

    return stage_win_numbers, yellow_stage_numbers


def build_rider_stage_history(
    event: Event,
    current_stage: Stage,
    event_riders: list[EventRider],
) -> dict[int, RiderStageHistory]:
    event_rider_ids = [event_rider.id for event_rider in event_riders]
    if not event_rider_ids:
        return {}

    eligible_stages = [
        stage
        for stage in event.stages
        if stage.number < current_stage.number or (stage.id == current_stage.id and stage.has_ranked_result())
    ]
    if not eligible_stages:
        return {
            event_rider_id: RiderStageHistory(event_rider_id=event_rider_id, total_points=0, results=[])
            for event_rider_id in event_rider_ids
        }

    eligible_stage_numbers = [stage.number for stage in eligible_stages]
    scores_by_stage_id = {
        stage.id: build_official_stage_scores(stage)
        for stage in eligible_stages
    }

    results = (
        StageResult.query.join(Stage)
        .filter(
            Stage.event_id == event.id,
            Stage.number.in_(eligible_stage_numbers),
            StageResult.event_rider_id.in_(event_rider_ids),
        )
        .order_by(Stage.number)
        .all()
    )

    by_rider: dict[int, list[RiderStageHistoryItem]] = defaultdict(list)
    for result in results:
        rank_label = f"#{result.rank}" if result.rank else result.status
        official_score = scores_by_stage_id[result.stage_id].get(result.event_rider_id)
        by_rider[result.event_rider_id].append(
            RiderStageHistoryItem(
                stage_number=result.stage.number,
                stage_name=result.stage.name,
                rank_label=rank_label,
                points=official_score.total_points if official_score else result.base_points,
            )
        )

    return {
        event_rider_id: RiderStageHistory(
            event_rider_id=event_rider_id,
            total_points=sum(item.points for item in by_rider[event_rider_id]),
            results=by_rider[event_rider_id],
        )
        for event_rider_id in event_rider_ids
    }


def latest_finished_stage(event: Event) -> Stage | None:
    finished = [stage for stage in event.stages if stage.has_ranked_result()]
    return finished[-1] if finished else None


def current_yellow_user_ids(event: Event) -> set[int]:
    latest_stage = latest_finished_stage(event)
    if not latest_stage:
        return set()
    return {
        award.user_id
        for award in Award.query.filter_by(
            event_id=event.id,
            stage_id=latest_stage.id,
            award_type="yellow_jersey",
        )
    }


def can_edit_team(event: Event, now: datetime | None = None) -> bool:
    return event.status == "active" and not event.has_started(now)
