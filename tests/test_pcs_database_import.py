from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import BytesIO

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from tour_femmes import create_app, db
from tour_femmes.models import (
    ClassificationResult,
    Event,
    EventEntry,
    EventRider,
    Rider,
    Stage,
    StageLineup,
    StageLineupRider,
    StageResult,
    Team,
    TeamSelection,
    TeamSelectionRider,
    User,
    UserStageScore,
)
from tour_femmes.services.pcs_database_import import import_pcs_database


class TestConfig:
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    ADMIN_PASSWORD = "admin"
    PCS_BASE_URL = "https://www.procyclingstats.com"
    PCS_DIRECT_IMPORTS_ENABLED = False
    PCS_DATABASE_UPLOAD_MAX_BYTES = 8 * 1024 * 1024
    APP_TIMEZONE = "Europe/Amsterdam"


def test_pcs_database_merge_preserves_online_game_data(tmp_path):
    source_path = tmp_path / "local.sqlite3"
    _create_source_database(source_path)
    app = create_app(__name__ + ".TestConfig")

    with app.app_context():
        target_ids = _seed_target_database()
        report = import_pcs_database(source_path)
        db.session.commit()

        event = Event.query.filter_by(slug="test-race", year=2026).one()
        stage = Stage.query.filter_by(event_id=event.id, number=1).one()
        rider = Rider.query.filter_by(pcs_slug="renner-een").one()
        event_rider = EventRider.query.filter_by(event_id=event.id, rider_id=rider.id).one()
        selection = TeamSelection.query.one()
        lineup = StageLineup.query.one()

        assert event.id == target_ids["event_id"]
        assert stage.id == target_ids["stage_id"]
        assert event_rider.id == target_ids["event_rider_id"]
        assert event.name == "Online aangepaste naam"
        assert event.budget == 65
        assert event.team_size == 1
        assert event.lineup_size == 1
        assert stage.name == "Lokale PCS-etappe"
        assert rider.name == "Bijgewerkte Renner"
        assert rider.photo_url == "https://www.procyclingstats.com/images/rider.jpg"
        assert event_rider.price == 12

        assert User.query.count() == 1
        assert User.query.filter_by(username="online-user").one().id == target_ids["user_id"]
        assert User.query.filter_by(username="alleen-lokaal").first() is None
        assert EventEntry.query.count() == 1
        assert selection.id == target_ids["selection_id"]
        assert selection.rider_ids() == {target_ids["event_rider_id"]}
        assert lineup.id == target_ids["lineup_id"]
        assert lineup.rider_ids() == {target_ids["event_rider_id"]}
        assert lineup.captain_event_rider_id == target_ids["event_rider_id"]

        result = StageResult.query.filter_by(stage_id=stage.id, event_rider_id=event_rider.id).one()
        classification = ClassificationResult.query.filter_by(
            stage_id=stage.id,
            event_rider_id=event_rider.id,
            classification="gc",
        ).one()
        score = UserStageScore.query.filter_by(
            user_id=target_ids["user_id"],
            stage_id=stage.id,
        ).one()
        assert result.rank == 1
        assert classification.rank == 1
        assert score.score > 0
        assert report.stage_results_imported == 1
        assert report.classification_results_imported == 1
        assert report.scores_recalculated == 1


def test_admin_upload_rejects_non_sqlite_file():
    app = create_app(__name__ + ".TestConfig")
    client = app.test_client()
    _login_admin(client)

    response = client.post(
        "/admin/import-pcs-database",
        data={
            "csrf_token": "token",
            "confirm_pcs_only": "1",
            "database": (BytesIO(b"not a sqlite database"), "local.sqlite3"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "geen geldige SQLite-database" in response.get_data(as_text=True)


def test_online_admin_hides_and_blocks_direct_pcs_actions():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        event = Event(
            name="Online koers",
            slug="online-koers",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/online-koers/2026",
        )
        db.session.add(event)
        db.session.commit()
        event_id = event.id

    client = app.test_client()
    _login_admin(client)
    page = client.get(f"/admin/events/{event_id}")
    html = page.get_data(as_text=True)
    dashboard_html = client.get("/admin/").get_data(as_text=True)

    assert page.status_code == 200
    assert "Etappes laden uit PCS" not in html
    assert "Startlijst snel bijwerken" not in html
    assert "Naar database-upload" in html
    assert "Koersdata uploaden" in dashboard_html

    blocked = client.post(
        f"/admin/events/{event_id}/initialize",
        data={"csrf_token": "token"},
        follow_redirects=True,
    )
    assert blocked.status_code == 200
    assert "Directe PCS-imports zijn op deze omgeving uitgeschakeld" in blocked.get_data(
        as_text=True
    )


def _seed_target_database() -> dict[str, int]:
    db.create_all()
    user = User(username="online-user", password_hash="hash")
    event = Event(
        name="Online aangepaste naam",
        slug="test-race",
        year=2026,
        pcs_url="https://www.procyclingstats.com/race/test-race/2026",
        budget=65,
        team_size=1,
        lineup_size=1,
    )
    stage = Stage(
        event=event,
        number=1,
        name="Oude etappenaam",
        starts_at=datetime.now(timezone.utc) - timedelta(hours=2),
        pcs_url=f"{event.pcs_url}/stage-1",
    )
    team = Team(event=event, name="Testploeg")
    rider = Rider(
        pcs_slug="renner-een",
        pcs_url="https://www.procyclingstats.com/rider/renner-een",
        name="Oude Renner",
    )
    event_rider = EventRider(event=event, rider=rider, team=team, price=5)
    entry = EventEntry(user=user, event=event)
    selection = TeamSelection(user=user, event=event, total_price=5)
    selection.riders.append(TeamSelectionRider(event_rider=event_rider))
    lineup = StageLineup(user=user, stage=stage, captain=event_rider)
    lineup.riders.append(StageLineupRider(event_rider=event_rider))
    db.session.add_all([entry, selection, lineup])
    db.session.commit()
    return {
        "user_id": user.id,
        "event_id": event.id,
        "stage_id": stage.id,
        "event_rider_id": event_rider.id,
        "selection_id": selection.id,
        "lineup_id": lineup.id,
    }


def _create_source_database(source_path) -> None:
    source_engine = create_engine(f"sqlite:///{source_path}")
    db.metadata.create_all(source_engine)
    with Session(source_engine) as source:
        event = Event(
            id=50,
            name="Lokale PCS-naam",
            slug="test-race",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/test-race/2026",
            budget=999,
            team_size=11,
            lineup_size=6,
        )
        stage = Stage(
            id=60,
            event=event,
            number=1,
            name="Lokale PCS-etappe",
            starts_at=datetime.now(timezone.utc) - timedelta(hours=1),
            pcs_url=f"{event.pcs_url}/stage-1",
            distance_km=132.5,
            parcours_type="Heuvel",
            profile_image_url="https://www.procyclingstats.com/images/profile.jpg",
        )
        team = Team(
            id=70,
            event=event,
            name="Testploeg",
            image_url="https://www.procyclingstats.com/images/team.png",
        )
        rider = Rider(
            id=80,
            pcs_slug="renner-een",
            pcs_url="https://www.procyclingstats.com/rider/renner-een",
            name="Bijgewerkte Renner",
            photo_url="https://www.procyclingstats.com/images/rider.jpg",
            specialties={"sprint": 75},
            best_results=[{"name": "Testzege"}],
            grand_tour_results={"tour": [{"year": 2025, "result": "12"}]},
        )
        event_rider = EventRider(
            id=90,
            event=event,
            rider=rider,
            team=team,
            price=12,
        )
        result = StageResult(
            id=100,
            stage=stage,
            event_rider=event_rider,
            rank=1,
            status="FIN",
            raw_result={"name": rider.name},
        )
        classification = ClassificationResult(
            id=110,
            stage=stage,
            event_rider=event_rider,
            classification="gc",
            rank=1,
        )
        local_only_user = User(
            id=120,
            username="alleen-lokaal",
            password_hash="niet-importeren",
        )
        source.add_all([event, stage, team, rider, event_rider, result, classification, local_only_user])
        source.commit()
    source_engine.dispose()


def _login_admin(client) -> None:
    with client.session_transaction() as session:
        session["admin_ok"] = True
        session["_csrf_token"] = "token"
