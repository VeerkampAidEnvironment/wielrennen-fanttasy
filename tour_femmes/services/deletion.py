from __future__ import annotations

from sqlalchemy import false

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
    Subleague,
    SubleagueMember,
    Team,
    TeamSelection,
    TeamSelectionRider,
    User,
    UserStageRiderScore,
    UserStageScore,
)


def delete_event_game(event: Event) -> dict[str, int]:
    """Delete an event and all event-bound game data in FK-safe order."""
    event_id = event.id
    stage_ids = _ids(db.session.query(Stage.id).filter(Stage.event_id == event_id))
    event_rider_ids = _ids(db.session.query(EventRider.id).filter(EventRider.event_id == event_id))
    selection_ids = _ids(db.session.query(TeamSelection.id).filter(TeamSelection.event_id == event_id))
    lineup_ids = _ids(
        db.session.query(StageLineup.id)
        .join(Stage, StageLineup.stage_id == Stage.id)
        .filter(Stage.event_id == event_id)
    )
    score_ids = _ids(
        db.session.query(UserStageScore.id)
        .join(Stage, UserStageScore.stage_id == Stage.id)
        .filter(Stage.event_id == event_id)
    )
    subleague_ids = _ids(
        db.session.query(Subleague.id).filter(Subleague.event_id == event_id)
    )

    counts = {
        "awards": _delete(Award.query.filter(Award.event_id == event_id)),
        "rider_scores": _delete(
            UserStageRiderScore.query.filter(
                _in(UserStageRiderScore.user_stage_score_id, score_ids)
                | _in(UserStageRiderScore.event_rider_id, event_rider_ids)
            )
        ),
        "user_scores": _delete(UserStageScore.query.filter(_in(UserStageScore.id, score_ids))),
        "lineup_riders": _delete(
            StageLineupRider.query.filter(
                _in(StageLineupRider.lineup_id, lineup_ids)
                | _in(StageLineupRider.event_rider_id, event_rider_ids)
            )
        ),
        "lineups": _delete(StageLineup.query.filter(_in(StageLineup.id, lineup_ids))),
        "selection_riders": _delete(
            TeamSelectionRider.query.filter(
                _in(TeamSelectionRider.selection_id, selection_ids)
                | _in(TeamSelectionRider.event_rider_id, event_rider_ids)
            )
        ),
        "selections": _delete(TeamSelection.query.filter(_in(TeamSelection.id, selection_ids))),
        "stage_results": _delete(
            StageResult.query.filter(
                _in(StageResult.stage_id, stage_ids)
                | _in(StageResult.event_rider_id, event_rider_ids)
            )
        ),
        "classification_results": _delete(
            ClassificationResult.query.filter(
                _in(ClassificationResult.stage_id, stage_ids)
                | _in(ClassificationResult.event_rider_id, event_rider_ids)
            )
        ),
        "subleague_members": _delete(
            SubleagueMember.query.filter(_in(SubleagueMember.subleague_id, subleague_ids))
        ),
        "subleagues": _delete(
            Subleague.query.filter(Subleague.event_id == event_id)
        ),
        "entries": _delete(EventEntry.query.filter(EventEntry.event_id == event_id)),
        "stages": _delete(Stage.query.filter(Stage.event_id == event_id)),
        "event_riders": _delete(EventRider.query.filter(EventRider.event_id == event_id)),
        "teams": _delete(Team.query.filter(Team.event_id == event_id)),
    }
    db.session.delete(event)
    counts["events"] = 1
    return counts


def delete_user_account(user: User) -> dict[str, int]:
    """Delete a user account and recalculate awards for affected events."""
    user_id = user.id
    affected_event_ids = _affected_event_ids_for_user(user_id)
    selection_ids = _ids(db.session.query(TeamSelection.id).filter(TeamSelection.user_id == user_id))
    lineup_ids = _ids(db.session.query(StageLineup.id).filter(StageLineup.user_id == user_id))
    score_ids = _ids(db.session.query(UserStageScore.id).filter(UserStageScore.user_id == user_id))
    owned_subleague_ids = _ids(
        db.session.query(Subleague.id).filter(Subleague.owner_id == user_id)
    )

    counts = {
        "awards": _delete(Award.query.filter(Award.user_id == user_id)),
        "rider_scores": _delete(
            UserStageRiderScore.query.filter(_in(UserStageRiderScore.user_stage_score_id, score_ids))
        ),
        "user_scores": _delete(UserStageScore.query.filter(UserStageScore.user_id == user_id)),
        "lineup_riders": _delete(StageLineupRider.query.filter(_in(StageLineupRider.lineup_id, lineup_ids))),
        "lineups": _delete(StageLineup.query.filter(StageLineup.user_id == user_id)),
        "selection_riders": _delete(
            TeamSelectionRider.query.filter(_in(TeamSelectionRider.selection_id, selection_ids))
        ),
        "selections": _delete(TeamSelection.query.filter(TeamSelection.user_id == user_id)),
        "subleague_members": _delete(
            SubleagueMember.query.filter(
                (SubleagueMember.user_id == user_id)
                | _in(SubleagueMember.subleague_id, owned_subleague_ids)
            )
        ),
        "subleagues": _delete(
            Subleague.query.filter(Subleague.owner_id == user_id)
        ),
        "entries": _delete(EventEntry.query.filter(EventEntry.user_id == user_id)),
    }
    db.session.delete(user)
    counts["users"] = 1
    db.session.flush()

    from tour_femmes.services.game import recalculate_event_awards

    for event_id in sorted(affected_event_ids):
        event = db.session.get(Event, event_id)
        if event:
            recalculate_event_awards(event)
    return counts


def _affected_event_ids_for_user(user_id: int) -> set[int]:
    event_ids = set(_ids(db.session.query(EventEntry.event_id).filter(EventEntry.user_id == user_id)))
    event_ids.update(_ids(db.session.query(TeamSelection.event_id).filter(TeamSelection.user_id == user_id)))
    event_ids.update(_ids(db.session.query(Award.event_id).filter(Award.user_id == user_id)))
    event_ids.update(
        _ids(
            db.session.query(Stage.event_id)
            .join(StageLineup, StageLineup.stage_id == Stage.id)
            .filter(StageLineup.user_id == user_id)
        )
    )
    event_ids.update(
        _ids(
            db.session.query(Stage.event_id)
            .join(UserStageScore, UserStageScore.stage_id == Stage.id)
            .filter(UserStageScore.user_id == user_id)
        )
    )
    return event_ids


def _ids(query) -> list[int]:
    return [row[0] for row in query.all()]


def _in(column, values: list[int]):
    return column.in_(values) if values else false()


def _delete(query) -> int:
    return query.delete(synchronize_session=False)
