from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.engine import Connection

from tour_femmes import db
from tour_femmes.models import (
    ClassificationResult,
    Event,
    EventRider,
    Rider,
    Stage,
    StageResult,
    Team,
)
from tour_femmes.services.game import recalculate_stage_scores


class PcsDatabaseImportError(ValueError):
    pass


@dataclass(frozen=True)
class PcsDatabaseImportReport:
    events_created: int = 0
    events_updated: int = 0
    stages_created: int = 0
    stages_updated: int = 0
    teams_created: int = 0
    teams_updated: int = 0
    riders_created: int = 0
    riders_updated: int = 0
    event_riders_created: int = 0
    event_riders_updated: int = 0
    stage_results_imported: int = 0
    classification_results_imported: int = 0
    results_removed: int = 0
    scores_recalculated: int = 0

    def summary(self) -> str:
        return (
            f"{self.events_created + self.events_updated} koersen, "
            f"{self.stages_created + self.stages_updated} etappes, "
            f"{self.riders_created + self.riders_updated} renners, "
            f"{self.event_riders_created + self.event_riders_updated} startlijstregels, "
            f"{self.stage_results_imported} uitslagen en "
            f"{self.classification_results_imported} klassementsregels verwerkt. "
            f"Scores voor {self.scores_recalculated} etappes herberekend."
        )


# These are the only source tables this importer is allowed to read.
PCS_SOURCE_MODELS = (
    Event,
    Stage,
    Team,
    Rider,
    EventRider,
    StageResult,
    ClassificationResult,
)

EVENT_PCS_FIELDS = ("pcs_url",)
STAGE_PCS_FIELDS = (
    "name",
    "starts_at",
    "pcs_url",
    "live_url",
    "distance_km",
    "profile_score",
    "vertical_meters",
    "parcours_type",
    "departure",
    "arrival",
    "profile_image_url",
    "profile_image_data",
    "profile_image_mime",
    "is_finished",
    "results_imported_at",
)
TEAM_PCS_FIELDS = ("pcs_url", "image_url", "image_data", "image_mime", "category")
RIDER_PCS_FIELDS = (
    "pcs_url",
    "name",
    "photo_url",
    "photo_data",
    "photo_mime",
    "nationality",
    "date_of_birth",
    "height_m",
    "weight_kg",
    "specialties",
    "best_results",
    "grand_tour_results",
)
EVENT_RIDER_PCS_FIELDS = (
    "price",
    "active",
    "frozen",
    "startlist_status",
    "imported_at",
)
STAGE_RESULT_FIELDS = ("rank", "status", "time_gap", "raw_result", "base_points", "imported_at")
CLASSIFICATION_RESULT_FIELDS = ("rank", "is_final", "imported_at")


def import_pcs_database(source_path: str | Path) -> PcsDatabaseImportReport:
    """Merge local race data into the current database without reading user tables."""
    source_path = Path(source_path).resolve()
    _validate_sqlite_file(source_path)
    source_engine = _read_only_sqlite_engine(source_path)

    try:
        _validate_source_schema(source_engine)
        with source_engine.connect() as source:
            source_rows = {
                model.__tablename__: _read_rows(source, model)
                for model in PCS_SOURCE_MODELS
            }
        return _merge_source_rows(source_rows)
    finally:
        source_engine.dispose()


def _merge_source_rows(source_rows: dict[str, list[dict]]) -> PcsDatabaseImportReport:
    counts = {
        "events_created": 0,
        "events_updated": 0,
        "stages_created": 0,
        "stages_updated": 0,
        "teams_created": 0,
        "teams_updated": 0,
        "riders_created": 0,
        "riders_updated": 0,
        "event_riders_created": 0,
        "event_riders_updated": 0,
        "stage_results_imported": 0,
        "classification_results_imported": 0,
        "results_removed": 0,
        "scores_recalculated": 0,
    }
    event_map: dict[int, Event] = {}
    stage_map: dict[int, Stage] = {}
    team_map: dict[int, Team] = {}
    rider_map: dict[int, Rider] = {}
    event_rider_map: dict[int, EventRider] = {}

    event_rows = sorted(source_rows["event"], key=lambda row: row["id"])
    stage_rows = sorted(source_rows["stage"], key=lambda row: (row["event_id"], row["number"]))
    team_rows = sorted(source_rows["team"], key=lambda row: (row["event_id"], row["name"]))
    event_rider_rows = sorted(
        source_rows["event_rider"],
        key=lambda row: (row["event_id"], row["id"]),
    )
    referenced_rider_ids = {row["rider_id"] for row in event_rider_rows}
    rider_rows = [
        row for row in source_rows["rider"] if row["id"] in referenced_rider_ids
    ]

    for row in event_rows:
        target = Event.query.filter_by(slug=row["slug"], year=row["year"]).first()
        if target:
            _assign(target, row, EVENT_PCS_FIELDS)
            counts["events_updated"] += 1
        else:
            target = Event(
                name=row["name"],
                slug=row["slug"],
                year=row["year"],
                pcs_url=row["pcs_url"],
                budget=row["budget"],
                team_size=row["team_size"],
                lineup_size=row["lineup_size"],
                status=row["status"],
            )
            db.session.add(target)
            counts["events_created"] += 1
        event_map[row["id"]] = target
    db.session.flush()

    for row in stage_rows:
        event = _mapped(event_map, row["event_id"], "etappe", row["id"])
        target = Stage.query.filter_by(event_id=event.id, number=row["number"]).first()
        if target:
            _assign(target, row, STAGE_PCS_FIELDS)
            counts["stages_updated"] += 1
        else:
            target = Stage(event=event, number=row["number"], name=row["name"], pcs_url=row["pcs_url"])
            _assign(target, row, STAGE_PCS_FIELDS)
            db.session.add(target)
            counts["stages_created"] += 1
        stage_map[row["id"]] = target

    for row in team_rows:
        event = _mapped(event_map, row["event_id"], "ploeg", row["id"])
        target = Team.query.filter_by(event_id=event.id, name=row["name"]).first()
        if target:
            _assign(target, row, TEAM_PCS_FIELDS)
            counts["teams_updated"] += 1
        else:
            target = Team(event=event, name=row["name"])
            _assign(target, row, TEAM_PCS_FIELDS)
            db.session.add(target)
            counts["teams_created"] += 1

        team_map[row["id"]] = target

    for row in rider_rows:
        target = Rider.query.filter_by(pcs_slug=row["pcs_slug"]).first()
        if target:
            _assign(target, row, RIDER_PCS_FIELDS)
            counts["riders_updated"] += 1
        else:
            target = Rider(
                pcs_slug=row["pcs_slug"],
                pcs_url=row["pcs_url"],
                name=row["name"],
            )
            _assign(target, row, RIDER_PCS_FIELDS)
            db.session.add(target)
            counts["riders_created"] += 1
        rider_map[row["id"]] = target
    db.session.flush()

    for row in event_rider_rows:
        event = _mapped(event_map, row["event_id"], "startlijstregel", row["id"])
        rider = _mapped(rider_map, row["rider_id"], "startlijstregel", row["id"])
        team = team_map.get(row["team_id"]) if row["team_id"] is not None else None
        target = EventRider.query.filter_by(event_id=event.id, rider_id=rider.id).first()
        if target:
            _assign(target, row, EVENT_RIDER_PCS_FIELDS)
            counts["event_riders_updated"] += 1
        else:
            target = EventRider(event=event, rider=rider)
            _assign(target, row, EVENT_RIDER_PCS_FIELDS)
            db.session.add(target)
            counts["event_riders_created"] += 1
        target.team = team
        event_rider_map[row["id"]] = target
    db.session.flush()

    result_rows_by_stage = _group_by(source_rows["stage_result"], "stage_id")
    classification_rows_by_stage = _group_by(source_rows["classification_result"], "stage_id")
    touched_source_stage_ids = set(result_rows_by_stage) | set(classification_rows_by_stage)
    touched_stages: list[Stage] = []

    for source_stage_id in sorted(
        touched_source_stage_ids,
        key=lambda stage_id: stage_map[stage_id].number if stage_id in stage_map else stage_id,
    ):
        stage = _mapped(stage_map, source_stage_id, "uitslag", source_stage_id)
        touched_stages.append(stage)

        source_result_keys: set[int] = set()
        existing_results = {
            result.event_rider_id: result
            for result in StageResult.query.filter_by(stage_id=stage.id).all()
        }
        for row in result_rows_by_stage.get(source_stage_id, []):
            event_rider = _mapped(event_rider_map, row["event_rider_id"], "uitslag", row["id"])
            _validate_same_event(stage, event_rider, "uitslag", row["id"])
            source_result_keys.add(event_rider.id)
            target = existing_results.get(event_rider.id)
            if not target:
                target = StageResult(stage=stage, event_rider=event_rider)
                db.session.add(target)
            _assign(target, row, STAGE_RESULT_FIELDS)
            counts["stage_results_imported"] += 1
        for event_rider_id, target in existing_results.items():
            if event_rider_id not in source_result_keys:
                db.session.delete(target)
                counts["results_removed"] += 1

        source_classification_keys: set[tuple[int, str]] = set()
        existing_classifications = {
            (result.event_rider_id, result.classification): result
            for result in ClassificationResult.query.filter_by(stage_id=stage.id).all()
        }
        for row in classification_rows_by_stage.get(source_stage_id, []):
            event_rider = _mapped(
                event_rider_map,
                row["event_rider_id"],
                "klassementsuitslag",
                row["id"],
            )
            _validate_same_event(stage, event_rider, "klassementsuitslag", row["id"])
            key = (event_rider.id, row["classification"])
            source_classification_keys.add(key)
            target = existing_classifications.get(key)
            if not target:
                target = ClassificationResult(
                    stage=stage,
                    event_rider=event_rider,
                    classification=row["classification"],
                )
                db.session.add(target)
            _assign(target, row, CLASSIFICATION_RESULT_FIELDS)
            counts["classification_results_imported"] += 1
        for key, target in existing_classifications.items():
            if key not in source_classification_keys:
                db.session.delete(target)
                counts["results_removed"] += 1

    db.session.flush()
    for stage in touched_stages:
        db.session.expire(stage, ["results", "classification_results"])
        recalculate_stage_scores(stage)
        counts["scores_recalculated"] += 1
    db.session.flush()
    return PcsDatabaseImportReport(**counts)


def _read_rows(source: Connection, model) -> list[dict]:
    return [dict(row) for row in source.execute(select(model.__table__)).mappings()]


def _validate_sqlite_file(source_path: Path) -> None:
    if not source_path.is_file():
        raise PcsDatabaseImportError("Het geüploade databasebestand bestaat niet.")
    with source_path.open("rb") as source:
        if source.read(16) != b"SQLite format 3\x00":
            raise PcsDatabaseImportError("Dit bestand is geen geldige SQLite-database.")


def _read_only_sqlite_engine(source_path: Path):
    sqlite_uri = f"file:{source_path.as_posix()}?mode=ro"
    return create_engine(
        "sqlite://",
        creator=lambda: sqlite3.connect(sqlite_uri, uri=True),
    )


def _validate_source_schema(source_engine) -> None:
    source_inspector = inspect(source_engine)
    available_tables = set(source_inspector.get_table_names())
    for model in PCS_SOURCE_MODELS:
        table_name = model.__tablename__
        if table_name not in available_tables:
            raise PcsDatabaseImportError(
                f"De brondatabase mist de vereiste tabel '{table_name}'."
            )
        available_columns = {
            column["name"] for column in source_inspector.get_columns(table_name)
        }
        required_columns = {column.name for column in model.__table__.columns}
        missing_columns = sorted(required_columns - available_columns)
        if missing_columns:
            raise PcsDatabaseImportError(
                f"Tabel '{table_name}' mist kolommen: {', '.join(missing_columns)}."
            )


def _assign(target, row: dict, fields: tuple[str, ...]) -> None:
    for field in fields:
        setattr(target, field, row[field])


def _mapped(mapping: dict[int, object], source_id: int, label: str, row_id: int):
    target = mapping.get(source_id)
    if target is None:
        raise PcsDatabaseImportError(
            f"Ongeldige {label} {row_id}: verwijzing {source_id} ontbreekt."
        )
    return target


def _validate_same_event(stage: Stage, event_rider: EventRider, label: str, row_id: int) -> None:
    if stage.event_id != event_rider.event_id:
        raise PcsDatabaseImportError(
            f"Ongeldige {label} {row_id}: renner en etappe horen niet bij dezelfde koers."
        )


def _group_by(rows: list[dict], key: str) -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row[key], []).append(row)
    return grouped
