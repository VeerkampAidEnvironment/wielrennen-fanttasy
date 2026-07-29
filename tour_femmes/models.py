from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Iterable

from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.mysql import MEDIUMBLOB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import deferred

from tour_femmes import db
from tour_femmes.timezones import app_timezone, app_timezone_name


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    entries = db.relationship("EventEntry", back_populates="user", cascade="all, delete-orphan")
    team_selections = db.relationship("TeamSelection", back_populates="user", cascade="all, delete-orphan")
    stage_lineups = db.relationship("StageLineup", back_populates="user", cascade="all, delete-orphan")
    stage_scores = db.relationship("UserStageScore", back_populates="user", cascade="all, delete-orphan")


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(160), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    pcs_url = db.Column(db.String(500), nullable=False)
    budget = db.Column(db.Integer, default=65, nullable=False)
    team_size = db.Column(db.Integer, default=11, nullable=False)
    lineup_size = db.Column(db.Integer, default=6, nullable=False)
    status = db.Column(db.String(30), default="active", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    stages = db.relationship(
        "Stage",
        back_populates="event",
        order_by="Stage.number",
        cascade="all, delete-orphan",
    )
    teams = db.relationship("Team", back_populates="event", cascade="all, delete-orphan")
    event_riders = db.relationship("EventRider", back_populates="event", cascade="all, delete-orphan")
    entries = db.relationship("EventEntry", back_populates="event", cascade="all, delete-orphan")
    awards = db.relationship("Award", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("slug", "year", name="uq_event_slug_year"),)

    def first_stage(self) -> Stage | None:
        return self.stages[0] if self.stages else None

    @hybrid_property
    def starts_at(self) -> datetime | None:
        first = self.first_stage()
        return first.starts_at if first else None

    def has_started(self, now: datetime | None = None) -> bool:
        first = self.first_stage()
        if not first or not first.starts_at:
            return False
        now = now or utcnow()
        return _coerce_aware(first.starts_at) <= now

    def display_status(self, now: datetime | None = None) -> str:
        if self.status != "active":
            return {"draft": "Concept", "finished": "Afgelopen", "archived": "Gearchiveerd"}.get(
                self.status,
                self.status.title(),
            )
        if self.stages and all(stage.is_finished for stage in self.stages):
            return "Afgelopen"
        return "Gestart" if self.has_started(now) else "Nog niet gestart"

    def next_stage(self, now: datetime | None = None) -> Stage | None:
        now = now or utcnow()
        upcoming = [
            stage
            for stage in self.stages
            if stage.starts_at is None or _coerce_aware(stage.starts_at) > now
        ]
        return upcoming[0] if upcoming else None

    def live_stage(
        self,
        now: datetime | None = None,
        timezone_name: str | None = None,
    ) -> Stage | None:
        """Return the only stage whose PCS live page may be shown today."""
        timezone_name = timezone_name or _app_timezone_name()
        local_timezone = app_timezone(timezone_name)
        local_now = _coerce_aware(now or utcnow()).astimezone(local_timezone)
        today_stages = [
            stage
            for stage in self.stages
            if stage.starts_at
            and _coerce_aware(stage.starts_at).astimezone(local_timezone).date() == local_now.date()
            and not stage.is_finished
            and not stage.has_ranked_result()
        ]
        if not today_stages:
            return None

        started = [
            stage
            for stage in today_stages
            if _coerce_aware(stage.starts_at).astimezone(local_timezone) <= local_now
        ]
        if started:
            return max(started, key=lambda stage: _coerce_aware(stage.starts_at))
        return min(today_stages, key=lambda stage: _coerce_aware(stage.starts_at))


class Stage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False, index=True)
    number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(220), nullable=False)
    starts_at = db.Column(db.DateTime(timezone=True), nullable=True)
    pcs_url = db.Column(db.String(500), nullable=False)
    live_url = db.Column(db.String(500), nullable=True)
    distance_km = db.Column(db.Float, nullable=True)
    profile_score = db.Column(db.Integer, nullable=True)
    vertical_meters = db.Column(db.Integer, nullable=True)
    parcours_type = db.Column(db.String(80), nullable=True)
    departure = db.Column(db.String(120), nullable=True)
    arrival = db.Column(db.String(120), nullable=True)
    profile_image_url = db.Column(db.String(500), nullable=True)
    profile_image_data = deferred(
        db.Column(
            db.LargeBinary().with_variant(MEDIUMBLOB(), "mysql"),
            nullable=True,
        )
    )
    profile_image_mime = db.Column(db.String(80), nullable=True)
    is_finished = db.Column(db.Boolean, default=False, nullable=False)
    results_imported_at = db.Column(db.DateTime(timezone=True), nullable=True)
    live_imported_at = db.Column(db.DateTime(timezone=True), nullable=True)

    event = db.relationship("Event", back_populates="stages")
    lineups = db.relationship("StageLineup", back_populates="stage", cascade="all, delete-orphan")
    results = db.relationship(
        "StageResult",
        back_populates="stage",
        order_by="StageResult.rank",
        cascade="all, delete-orphan",
    )
    user_scores = db.relationship("UserStageScore", back_populates="stage", cascade="all, delete-orphan")
    classification_results = db.relationship(
        "ClassificationResult",
        back_populates="stage",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("event_id", "number", name="uq_stage_event_number"),)

    def is_locked(self, now: datetime | None = None) -> bool:
        if not self.starts_at:
            return False
        now = now or utcnow()
        return _coerce_aware(self.starts_at) <= now

    def has_ranked_result(self) -> bool:
        return any(result.rank and result.status not in NON_FINISH_STATUSES for result in self.results)

    def deadline_timestamp_ms(self) -> int | None:
        if not self.starts_at:
            return None
        return round(_coerce_aware(self.starts_at).timestamp() * 1000)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    pcs_url = db.Column(db.String(500), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    image_data = deferred(
        db.Column(
            db.LargeBinary().with_variant(MEDIUMBLOB(), "mysql"),
            nullable=True,
        )
    )
    image_mime = db.Column(db.String(80), nullable=True)
    category = db.Column(db.String(30), nullable=True)

    event = db.relationship("Event", back_populates="teams")
    event_riders = db.relationship("EventRider", back_populates="team")

    __table_args__ = (UniqueConstraint("event_id", "name", name="uq_team_event_name"),)


class Rider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pcs_slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    pcs_url = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(180), nullable=False, index=True)
    photo_url = db.Column(db.String(500), nullable=True)
    photo_data = deferred(
        db.Column(
            db.LargeBinary().with_variant(MEDIUMBLOB(), "mysql"),
            nullable=True,
        )
    )
    photo_mime = db.Column(db.String(80), nullable=True)
    nationality = db.Column(db.String(80), nullable=True)
    date_of_birth = db.Column(db.String(80), nullable=True)
    height_m = db.Column(db.Float, nullable=True)
    weight_kg = db.Column(db.Float, nullable=True)
    specialties = db.Column(db.JSON, default=dict, nullable=False)
    best_results = db.Column(db.JSON, default=list, nullable=False)
    grand_tour_results = db.Column(db.JSON, default=dict, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    event_links = db.relationship("EventRider", back_populates="rider", cascade="all, delete-orphan")

    @property
    def age(self) -> int | None:
        return age_from_birth_date(self.date_of_birth)


class EventRider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False, index=True)
    rider_id = db.Column(db.Integer, db.ForeignKey("rider.id"), nullable=False, index=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True, index=True)
    price = db.Column(db.Integer, nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    frozen = db.Column(db.Boolean, default=False, nullable=False)
    startlist_status = db.Column(db.String(30), default="listed", nullable=False)
    imported_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    event = db.relationship("Event", back_populates="event_riders")
    rider = db.relationship("Rider", back_populates="event_links")
    team = db.relationship("Team", back_populates="event_riders")
    selection_links = db.relationship("TeamSelectionRider", back_populates="event_rider")
    lineup_links = db.relationship("StageLineupRider", back_populates="event_rider")
    stage_results = db.relationship("StageResult", back_populates="event_rider")
    user_stage_rider_scores = db.relationship("UserStageRiderScore", back_populates="event_rider")

    __table_args__ = (UniqueConstraint("event_id", "rider_id", name="uq_event_rider"),)

    @property
    def selectable(self) -> bool:
        return self.active and not self.frozen and self.price is not None


class EventEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False, index=True)
    joined_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    status = db.Column(db.String(30), default="active", nullable=False)

    user = db.relationship("User", back_populates="entries")
    event = db.relationship("Event", back_populates="entries")

    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_entry_user_event"),)


class TeamSelection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False, index=True)
    submitted_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    total_price = db.Column(db.Integer, default=0, nullable=False)

    user = db.relationship("User", back_populates="team_selections")
    event = db.relationship("Event")
    riders = db.relationship(
        "TeamSelectionRider",
        back_populates="selection",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_selection_user_event"),)

    def rider_ids(self) -> set[int]:
        return {link.event_rider_id for link in self.riders}


class TeamSelectionRider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    selection_id = db.Column(db.Integer, db.ForeignKey("team_selection.id"), nullable=False, index=True)
    event_rider_id = db.Column(db.Integer, db.ForeignKey("event_rider.id"), nullable=False, index=True)

    selection = db.relationship("TeamSelection", back_populates="riders")
    event_rider = db.relationship("EventRider", back_populates="selection_links")

    __table_args__ = (UniqueConstraint("selection_id", "event_rider_id", name="uq_selection_rider"),)


class StageLineup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("stage.id"), nullable=False, index=True)
    captain_event_rider_id = db.Column(db.Integer, db.ForeignKey("event_rider.id"), nullable=False)
    submitted_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    user = db.relationship("User", back_populates="stage_lineups")
    stage = db.relationship("Stage", back_populates="lineups")
    captain = db.relationship("EventRider")
    riders = db.relationship(
        "StageLineupRider",
        back_populates="lineup",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("user_id", "stage_id", name="uq_lineup_user_stage"),)

    def rider_ids(self) -> set[int]:
        return {link.event_rider_id for link in self.riders}


class StageLineupRider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lineup_id = db.Column(db.Integer, db.ForeignKey("stage_lineup.id"), nullable=False, index=True)
    event_rider_id = db.Column(db.Integer, db.ForeignKey("event_rider.id"), nullable=False, index=True)

    lineup = db.relationship("StageLineup", back_populates="riders")
    event_rider = db.relationship("EventRider", back_populates="lineup_links")

    __table_args__ = (UniqueConstraint("lineup_id", "event_rider_id", name="uq_lineup_rider"),)


class StageResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("stage.id"), nullable=False, index=True)
    event_rider_id = db.Column(db.Integer, db.ForeignKey("event_rider.id"), nullable=False, index=True)
    rank = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default="FIN", nullable=False)
    time_gap = db.Column(db.String(40), nullable=True)
    raw_result = db.Column(db.JSON, default=dict, nullable=False)
    base_points = db.Column(db.Integer, default=0, nullable=False)
    imported_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    stage = db.relationship("Stage", back_populates="results")
    event_rider = db.relationship("EventRider", back_populates="stage_results")

    __table_args__ = (UniqueConstraint("stage_id", "event_rider_id", name="uq_result_stage_rider"),)


class UserStageScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("stage.id"), nullable=False, index=True)
    score = db.Column(db.Integer, default=0, nullable=False)
    captain_bonus = db.Column(db.Integer, default=0, nullable=False)
    calculated_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    user = db.relationship("User", back_populates="stage_scores")
    stage = db.relationship("Stage", back_populates="user_scores")
    rider_scores = db.relationship(
        "UserStageRiderScore",
        back_populates="score",
        cascade="all, delete-orphan",
        order_by="UserStageRiderScore.total_points.desc()",
    )

    __table_args__ = (UniqueConstraint("user_id", "stage_id", name="uq_score_user_stage"),)


class UserStageRiderScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_stage_score_id = db.Column(db.Integer, db.ForeignKey("user_stage_score.id"), nullable=False, index=True)
    event_rider_id = db.Column(db.Integer, db.ForeignKey("event_rider.id"), nullable=False, index=True)
    rank = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=True)
    base_points = db.Column(db.Integer, default=0, nullable=False)
    captain_bonus = db.Column(db.Integer, default=0, nullable=False)
    classification_points = db.Column(db.Integer, default=0, nullable=False)
    teammate_points = db.Column(db.Integer, default=0, nullable=False)
    final_classification_points = db.Column(db.Integer, default=0, nullable=False)
    final_teammate_points = db.Column(db.Integer, default=0, nullable=False)
    total_points = db.Column(db.Integer, default=0, nullable=False)

    score = db.relationship("UserStageScore", back_populates="rider_scores")
    event_rider = db.relationship("EventRider", back_populates="user_stage_rider_scores")

    __table_args__ = (
        UniqueConstraint("user_stage_score_id", "event_rider_id", name="uq_rider_score_once"),
    )


class ClassificationResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("stage.id"), nullable=False, index=True)
    event_rider_id = db.Column(db.Integer, db.ForeignKey("event_rider.id"), nullable=False, index=True)
    classification = db.Column(db.String(20), nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    is_final = db.Column(db.Boolean, default=False, nullable=False)
    imported_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    stage = db.relationship("Stage", back_populates="classification_results")
    event_rider = db.relationship("EventRider")

    __table_args__ = (
        UniqueConstraint(
            "stage_id",
            "event_rider_id",
            "classification",
            name="uq_classification_stage_rider",
        ),
    )


class Award(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False, index=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("stage.id"), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    award_type = db.Column(db.String(30), nullable=False)
    awarded_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    event = db.relationship("Event", back_populates="awards")
    stage = db.relationship("Stage")
    user = db.relationship("User")

    __table_args__ = (
        UniqueConstraint("event_id", "stage_id", "user_id", "award_type", name="uq_award_once"),
    )


NON_FINISH_STATUSES = {"DNF", "DNS", "DSQ", "OTL", "DF", "NR"}


def _coerce_aware(value: datetime) -> datetime:
    if value.tzinfo:
        return value
    return value.replace(tzinfo=app_timezone(_app_timezone_name()))


def _app_timezone_name() -> str:
    return app_timezone_name()


def total_price(event_riders: Iterable[EventRider]) -> int:
    return sum(rider.price or 0 for rider in event_riders)


def age_from_birth_date(value: str | None) -> int | None:
    if not value:
        return None
    cleaned = re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", r"\1", value, flags=re.I)
    cleaned = re.sub(r"\s*\([^)]*\)\s*", " ", cleaned).strip()
    for fmt in ("%d %B %Y", "%d %b %Y", "%Y-%m-%d"):
        try:
            born = datetime.strptime(cleaned, fmt).date()
            break
        except ValueError:
            continue
    else:
        return None

    today = utcnow().date()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
