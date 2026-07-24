from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash

from tour_femmes import create_app, db
from tour_femmes.models import (
    Event,
    EventEntry,
    EventRider,
    Rider,
    StageResult,
    Stage,
    StageLineup,
    StageLineupRider,
    Team,
    TeamSelection,
    TeamSelectionRider,
    User,
    UserStageRiderScore,
    UserStageScore,
)
from tour_femmes.services.game import recalculate_stage_scores


class TestConfig:
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    ADMIN_PASSWORD = "admin"
    PCS_BASE_URL = "https://www.procyclingstats.com"
    APP_TIMEZONE = "Europe/Amsterdam"


def make_app_with_lineup_context():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        db.create_all()

        user = User(username="demo", email="demo@example.com", password_hash=generate_password_hash("demo"))
        event = Event(
            name="Testkoers",
            slug="testkoers",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/testkoers/2026",
            budget=65,
            team_size=11,
            lineup_size=6,
        )
        stage = Stage(
            event=event,
            number=1,
            name="Etappe 1",
            starts_at=datetime.now(timezone.utc) + timedelta(days=1),
            pcs_url=f"{event.pcs_url}/stage-1",
            profile_image_url="https://www.procyclingstats.com/images/profiles/test-stage-profile.jpg",
        )
        team = Team(
            event=event,
            name="Test Team",
            image_url="https://www.procyclingstats.com/images/shirts/test-team.png",
        )
        db.session.add_all([user, event, stage, team])
        db.session.flush()

        event_riders = []
        for index in range(11):
            rider = Rider(
                name=f"Renner {index}",
                pcs_slug=f"renner-{index}",
                pcs_url=f"https://www.procyclingstats.com/rider/renner-{index}",
                photo_url=f"https://www.procyclingstats.com/images/riders/test-renner-{index}.jpg",
            )
            event_rider = EventRider(event=event, rider=rider, team=team, price=1)
            db.session.add_all([rider, event_rider])
            event_riders.append(event_rider)

        db.session.flush()
        selection = TeamSelection(user=user, event=event, total_price=11)
        db.session.add_all([EventEntry(user=user, event=event), selection])
        db.session.flush()
        for event_rider in event_riders:
            selection.riders.append(TeamSelectionRider(event_rider=event_rider))

        event_rider_ids = [event_rider.id for event_rider in event_riders]
        db.session.commit()
        return app, user.id, event.id, stage.id, event_rider_ids


def login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True
        session["_csrf_token"] = "token"


def test_stage_lineup_fetch_autosaves_concept_and_complete_lineup():
    app, user_id, event_id, stage_id, event_rider_ids = make_app_with_lineup_context()
    client = app.test_client()
    login(client, user_id)

    concept_response = client.post(
        f"/events/{event_id}/stages/{stage_id}",
        data={
            "csrf_token": "token",
            "riders": [str(event_rider_id) for event_rider_id in event_rider_ids[:3]],
            "captain": str(event_rider_ids[0]),
        },
        headers={"Accept": "application/json", "X-Requested-With": "fetch"},
    )

    assert concept_response.status_code == 200
    assert concept_response.get_json()["complete"] is False
    with app.app_context():
        lineup = StageLineup.query.filter_by(user_id=user_id, stage_id=stage_id).one()
        assert lineup.rider_ids() == set(event_rider_ids[:3])

    complete_response = client.post(
        f"/events/{event_id}/stages/{stage_id}",
        data={
            "csrf_token": "token",
            "riders": [str(event_rider_id) for event_rider_id in event_rider_ids[:6]],
            "captain": str(event_rider_ids[1]),
        },
        headers={"Accept": "application/json", "X-Requested-With": "fetch"},
    )

    assert complete_response.status_code == 200
    assert complete_response.get_json()["complete"] is True
    with app.app_context():
        lineup = StageLineup.query.filter_by(user_id=user_id, stage_id=stage_id).one()
        assert lineup.rider_ids() == set(event_rider_ids[:6])
        assert lineup.captain_event_rider_id == event_rider_ids[1]


def test_stage_scoring_stores_user_and_rider_score_breakdown():
    app, user_id, _event_id, stage_id, event_rider_ids = make_app_with_lineup_context()

    with app.app_context():
        stage = db.session.get(Stage, stage_id)
        lineup = StageLineup(
            user_id=user_id,
            stage_id=stage_id,
            captain_event_rider_id=event_rider_ids[1],
        )
        db.session.add(lineup)
        db.session.flush()
        for event_rider_id in event_rider_ids[:6]:
            lineup.riders.append(StageLineupRider(event_rider_id=event_rider_id))

        db.session.add_all(
            [
                StageResult(stage_id=stage_id, event_rider_id=event_rider_ids[0], rank=1, status="FIN"),
                StageResult(stage_id=stage_id, event_rider_id=event_rider_ids[1], rank=2, status="FIN"),
                StageResult(stage_id=stage_id, event_rider_id=event_rider_ids[2], rank=10, status="FIN"),
            ]
        )
        db.session.flush()

        recalculate_stage_scores(stage)
        db.session.commit()

        score = UserStageScore.query.filter_by(user_id=user_id, stage_id=stage_id).one()
        assert score.score == 276
        assert score.captain_bonus == 80
        assert UserStageRiderScore.query.filter_by(user_stage_score_id=score.id).count() == 6

        captain_score = UserStageRiderScore.query.filter_by(
            user_stage_score_id=score.id,
            event_rider_id=event_rider_ids[1],
        ).one()
        assert captain_score.base_points == 80
        assert captain_score.captain_bonus == 80
        assert captain_score.total_points == 160


def test_scoring_rules_are_on_separate_tab_and_images_use_proxy():
    app, user_id, event_id, stage_id, _event_rider_ids = make_app_with_lineup_context()
    client = app.test_client()
    login(client, user_id)

    stage_response = client.get(f"/events/{event_id}/stages/{stage_id}")
    stage_html = stage_response.get_data(as_text=True)

    assert stage_response.status_code == 200
    assert "Etappeprofiel" in stage_html
    assert "Puntentelling</h2>" not in stage_html
    assert "/media/pcs-image?url=" in stage_html
    assert "Teamselectie" in stage_html
    assert "data-team-selection-tab" in stage_html
    assert "data-deadline-at=" in stage_html
    assert "data-deadline-countdown" in stage_html

    scoring_response = client.get(f"/events/{event_id}/scoring")
    scoring_html = scoring_response.get_data(as_text=True)

    assert scoring_response.status_code == 200
    assert "Puntentelling" in scoring_html
    assert "#18" in scoring_html

    team_response = client.get(f"/events/{event_id}/team")
    team_html = team_response.get_data(as_text=True)

    assert team_response.status_code == 200
    assert "Mijn team" in team_html
    assert "/media/pcs-image?url=" in team_html
    assert "data-deadline-at=" in team_html
    assert "data-hide-team-tab-on-expiry" in team_html


def test_team_selection_tab_disappears_after_stage_one_starts():
    app, user_id, event_id, stage_id, _event_rider_ids = make_app_with_lineup_context()
    with app.app_context():
        stage = db.session.get(Stage, stage_id)
        stage.starts_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.session.commit()

    client = app.test_client()
    login(client, user_id)

    team_html = client.get(f"/events/{event_id}/team").get_data(as_text=True)
    stage_html = client.get(f"/events/{event_id}/stages/{stage_id}").get_data(as_text=True)

    assert "data-team-selection-tab" not in team_html
    assert "data-team-selection-tab" not in stage_html
    assert "data-deadline-countdown" in team_html
    assert "data-deadline-countdown" in stage_html
