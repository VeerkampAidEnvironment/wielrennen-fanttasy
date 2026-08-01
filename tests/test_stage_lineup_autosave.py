from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash

from tour_femmes import create_app, db
from tour_femmes.models import (
    ClassificationResult,
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
from tour_femmes.services.game import (
    build_official_stage_scores,
    build_rider_stage_history,
    recalculate_stage_scores,
)
from tour_femmes.scoring import (
    DAILY_LEADER_TEAMMATE_POINTS,
    FINAL_WINNER_TEAMMATE_POINTS,
    STAGE_WINNER_TEAMMATE_POINTS,
    classification_points,
    points_for_result,
)


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
            profile_image_data=b"stored-stage-profile",
            profile_image_mime="image/jpeg",
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
                name="VOS Marianne" if index == 0 else f"Renner {index}",
                pcs_slug="marianne-vos" if index == 0 else f"renner-{index}",
                pcs_url=(
                    "https://www.procyclingstats.com/rider/marianne-vos"
                    if index == 0
                    else f"https://www.procyclingstats.com/rider/renner-{index}"
                ),
                photo_url=f"https://www.procyclingstats.com/images/riders/test-renner-{index}.jpg",
                photo_data=f"rider-{index}".encode(),
                photo_mime="image/jpeg",
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


def test_stage_profile_is_served_from_own_database():
    app, _user_id, _event_id, stage_id, _event_rider_ids = make_app_with_lineup_context()
    response = app.test_client().get(f"/media/stage-profile/{stage_id}")

    assert response.status_code == 200
    assert response.content_type == "image/jpeg"
    assert response.data == b"stored-stage-profile"


def test_rider_and_team_images_are_served_from_own_database():
    app, _user_id, _event_id, _stage_id, event_rider_ids = make_app_with_lineup_context()
    with app.app_context():
        event_rider = db.session.get(EventRider, event_rider_ids[0])
        event_rider.team.image_data = b"stored-team-image"
        event_rider.team.image_mime = "image/png"
        rider_id = event_rider.rider.id
        team_id = event_rider.team.id
        db.session.commit()

    client = app.test_client()
    rider_response = client.get(f"/media/rider-photo/{rider_id}")
    team_response = client.get(f"/media/team-image/{team_id}")

    assert rider_response.status_code == 200
    assert rider_response.data == b"rider-0"
    assert team_response.status_code == 200
    assert team_response.data == b"stored-team-image"


def test_stage_lineup_fetch_autosaves_concept_and_complete_lineup():
    app, user_id, event_id, stage_id, event_rider_ids = make_app_with_lineup_context()
    client = app.test_client()
    login(client, user_id)

    initial_html = client.get(
        f"/events/{event_id}/stages/{stage_id}"
    ).get_data(as_text=True)
    assert 'data-selection-state="complete"' in initial_html
    assert 'data-stage-selection-state="empty"' in initial_html

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
    concept_html = client.get(
        f"/events/{event_id}/stages/{stage_id}"
    ).get_data(as_text=True)
    assert 'data-stage-selection-state="partial"' in concept_html
    assert '<small class="event-tab-status">3/6</small>' in concept_html

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
    complete_html = client.get(
        f"/events/{event_id}/stages/{stage_id}"
    ).get_data(as_text=True)
    assert 'data-stage-selection-state="complete"' in complete_html
    assert complete_html.count('<small class="event-tab-status">Compleet</small>') == 2


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
        # 276 result points plus 5 teammates of the stage winner x 10.
        assert score.score == 326
        assert score.captain_bonus == 80
        assert UserStageRiderScore.query.filter_by(user_stage_score_id=score.id).count() == 6

        captain_score = UserStageRiderScore.query.filter_by(
            user_stage_score_id=score.id,
            event_rider_id=event_rider_ids[1],
        ).one()
        assert captain_score.base_points == 80
        assert captain_score.captain_bonus == 80
        assert captain_score.total_points == 160 + STAGE_WINNER_TEAMMATE_POINTS

        winning_teammate = UserStageRiderScore.query.filter_by(
            user_stage_score_id=score.id,
            event_rider_id=event_rider_ids[1],
        ).one()
        assert winning_teammate.teammate_points == STAGE_WINNER_TEAMMATE_POINTS
        assert winning_teammate.total_points == 160 + STAGE_WINNER_TEAMMATE_POINTS


def test_final_gc_rewards_daily_lineup_and_full_team_teammates():
    app, user_id, _event_id, stage_id, event_rider_ids = make_app_with_lineup_context()

    with app.app_context():
        stage = db.session.get(Stage, stage_id)
        lineup = StageLineup(
            user_id=user_id,
            stage_id=stage_id,
            captain_event_rider_id=event_rider_ids[0],
        )
        db.session.add(lineup)
        db.session.flush()
        for event_rider_id in event_rider_ids[:6]:
            lineup.riders.append(StageLineupRider(event_rider_id=event_rider_id))

        db.session.add(
            ClassificationResult(
                stage_id=stage_id,
                event_rider_id=event_rider_ids[0],
                classification="gc",
                rank=1,
                is_final=True,
            )
        )
        db.session.flush()

        recalculate_stage_scores(stage)
        db.session.commit()

        score = UserStageScore.query.filter_by(user_id=user_id, stage_id=stage_id).one()
        expected = (
            classification_points("gc", 1)
            + 5 * DAILY_LEADER_TEAMMATE_POINTS["gc"]
            + classification_points("gc", 1, final=True)
            + 10 * FINAL_WINNER_TEAMMATE_POINTS["gc"]
        )
        assert score.score == expected

        winner = UserStageRiderScore.query.filter_by(
            user_stage_score_id=score.id,
            event_rider_id=event_rider_ids[0],
        ).one()
        assert winner.classification_points == classification_points("gc", 1)
        assert winner.final_classification_points == 200
        assert winner.teammate_points == 0

        reserve_teammate = UserStageRiderScore.query.filter_by(
            user_stage_score_id=score.id,
            event_rider_id=event_rider_ids[10],
        ).one()
        assert reserve_teammate.teammate_points == 0
        assert reserve_teammate.final_teammate_points == FINAL_WINNER_TEAMMATE_POINTS["gc"]


def test_scoring_rules_are_on_separate_tab_and_images_use_database_routes():
    app, user_id, event_id, stage_id, _event_rider_ids = make_app_with_lineup_context()
    client = app.test_client()
    login(client, user_id)

    stage_response = client.get(f"/events/{event_id}/stages/{stage_id}")
    stage_html = stage_response.get_data(as_text=True)

    assert stage_response.status_code == 200
    assert "Etappeprofiel" in stage_html
    assert stage_html.index("Etappeprofiel") < stage_html.index("Etappeselectie")
    assert "upcoming-stage-lineup" in stage_html
    assert "Puntentelling</h2>" not in stage_html
    assert f"/media/stage-profile/{stage_id}" in stage_html
    assert "/media/rider-photo/" in stage_html
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
    assert "/media/rider-photo/" in team_html
    assert "Tour-scores 2022-2025" in team_html
    assert "754 ptn" in team_html
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


def test_stage_tabs_show_ongoing_and_finished_instead_of_selection_complete():
    app, user_id, event_id, stage_id, event_rider_ids = make_app_with_lineup_context()
    with app.app_context():
        stage = db.session.get(Stage, stage_id)
        stage.starts_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        lineup = StageLineup(
            user_id=user_id,
            stage_id=stage_id,
            captain_event_rider_id=event_rider_ids[0],
        )
        db.session.add(lineup)
        for event_rider_id in event_rider_ids[:6]:
            lineup.riders.append(StageLineupRider(event_rider_id=event_rider_id))
        db.session.commit()

    client = app.test_client()
    login(client, user_id)

    ongoing_html = client.get(
        f"/events/{event_id}/stages/{stage_id}"
    ).get_data(as_text=True)
    assert 'data-stage-selection-state="ongoing"' in ongoing_html
    assert 'data-stage-lifecycle-state="ongoing"' in ongoing_html
    assert '<small class="event-tab-status">Bezig</small>' in ongoing_html
    assert '<small class="event-tab-status">Compleet</small>' not in ongoing_html

    with app.app_context():
        db.session.add(
            StageResult(
                stage_id=stage_id,
                event_rider_id=event_rider_ids[0],
                rank=1,
                status="FIN",
            )
        )
        db.session.commit()

    finished_html = client.get(
        f"/events/{event_id}/stages/{stage_id}"
    ).get_data(as_text=True)
    assert 'data-stage-selection-state="finished"' in finished_html
    assert 'data-stage-lifecycle-state="finished"' in finished_html
    assert '<small class="event-tab-status">Afgelopen</small>' in finished_html
    assert '<small class="event-tab-status">Compleet</small>' not in finished_html


def test_result_import_button_stays_in_admin_environment():
    app, user_id, event_id, stage_id, _event_rider_ids = make_app_with_lineup_context()
    with app.app_context():
        stage = db.session.get(Stage, stage_id)
        stage.starts_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.session.commit()

    client = app.test_client()
    login(client, user_id)
    with client.session_transaction() as session:
        session["admin_ok"] = True

    stage_html = client.get(f"/events/{event_id}/stages/{stage_id}").get_data(as_text=True)
    admin_html = client.get(f"/admin/events/{event_id}").get_data(as_text=True)

    assert "Uitslag laden" not in stage_html
    assert f"/admin/stages/{stage_id}/import-results" not in stage_html
    assert "Uitslag laden" in admin_html
    assert f"/admin/stages/{stage_id}/import-results" in admin_html


def test_finished_stage_moves_profile_below_results():
    app, user_id, event_id, stage_id, event_rider_ids = make_app_with_lineup_context()
    with app.app_context():
        stage = db.session.get(Stage, stage_id)
        stage.starts_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        lineup = StageLineup(
            user_id=user_id,
            stage_id=stage_id,
            captain_event_rider_id=event_rider_ids[0],
        )
        db.session.add(lineup)
        db.session.flush()
        for event_rider_id in event_rider_ids[:6]:
            lineup.riders.append(
                StageLineupRider(event_rider_id=event_rider_id)
            )
        db.session.add(
            StageResult(
                stage_id=stage_id,
                event_rider_id=event_rider_ids[0],
                rank=1,
                status="FIN",
                base_points=100,
            )
        )
        db.session.flush()
        recalculate_stage_scores(stage)
        db.session.commit()

    client = app.test_client()
    login(client, user_id)
    stage_html = client.get(f"/events/{event_id}/stages/{stage_id}").get_data(as_text=True)

    assert "finished-stage-profile" in stage_html
    assert stage_html.index("Officiële uitslag") < stage_html.index("Etappeprofiel")
    assert "upcoming-stage-lineup" not in stage_html
    assert "Etappeselectie" not in stage_html
    assert "Wisselspelers" in stage_html
    assert "5 renners" in stage_html
    assert "Niet opgesteld en niet meegerekend in jouw etappescore." in stage_html


def test_official_result_combines_stage_classification_and_team_points():
    app, _user_id, event_id, stage_id, event_rider_ids = make_app_with_lineup_context()
    with app.app_context():
        stage = db.session.get(Stage, stage_id)
        db.session.add_all(
            [
                StageResult(
                    stage_id=stage_id,
                    event_rider_id=event_rider_ids[0],
                    rank=1,
                    status="FIN",
                ),
                StageResult(
                    stage_id=stage_id,
                    event_rider_id=event_rider_ids[1],
                    rank=2,
                    status="FIN",
                ),
                ClassificationResult(
                    stage_id=stage_id,
                    event_rider_id=event_rider_ids[0],
                    classification="gc",
                    rank=1,
                    is_final=False,
                ),
            ]
        )
        db.session.flush()

        official_scores = build_official_stage_scores(stage)
        event = db.session.get(Event, event_id)
        event_riders = [
            db.session.get(EventRider, event_rider_id)
            for event_rider_id in event_rider_ids[:2]
        ]
        rider_history = build_rider_stage_history(event, stage, event_riders)

        assert official_scores[event_rider_ids[0]].stage_points == 100
        assert official_scores[event_rider_ids[0]].classification_points == 16
        assert official_scores[event_rider_ids[0]].teammate_points == 0
        assert official_scores[event_rider_ids[0]].total_points == 116
        second_place_points = points_for_result(2, "FIN")
        assert official_scores[event_rider_ids[1]].stage_points == second_place_points
        assert official_scores[event_rider_ids[1]].classification_points == 0
        assert official_scores[event_rider_ids[1]].teammate_points == 24
        assert official_scores[event_rider_ids[1]].total_points == second_place_points + 24
        assert rider_history[event_rider_ids[0]].total_points == 116
        assert rider_history[event_rider_ids[0]].results[0].points == 116
        assert rider_history[event_rider_ids[1]].total_points == second_place_points + 24
        assert rider_history[event_rider_ids[1]].results[0].points == second_place_points + 24
