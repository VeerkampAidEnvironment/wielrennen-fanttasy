from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash

from tour_femmes import create_app, db
from tour_femmes.models import (
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
)
from tour_femmes.services.game import (
    build_leaderboard,
    build_stage_leaderboard,
    build_team_selection_overview,
    recalculate_stage_scores,
)


class TestConfig:
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    PCS_BASE_URL = "https://www.procyclingstats.com"
    APP_TIMEZONE = "Europe/Amsterdam"


def make_leaderboard_app():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        alpha = User(username="alpha", password_hash=generate_password_hash("test"))
        beta = User(username="beta", password_hash=generate_password_hash("test"))
        event = Event(
            name="Test Tour",
            slug="test-tour",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/test-tour/2026",
            team_size=1,
            lineup_size=1,
        )
        stage_one = Stage(
            event=event,
            number=1,
            name="Start › Finish",
            starts_at=datetime.now(timezone.utc) - timedelta(hours=2),
            pcs_url=f"{event.pcs_url}/stage-1",
        )
        stage_two = Stage(
            event=event,
            number=2,
            name="Future › Finish",
            starts_at=datetime.now(timezone.utc) + timedelta(days=1),
            pcs_url=f"{event.pcs_url}/stage-2",
        )
        team = Team(event=event, name="Test Team")
        rider_alpha = Rider(
            name="Alpha Rider",
            pcs_slug="alpha-rider",
            pcs_url="https://www.procyclingstats.com/rider/alpha-rider",
        )
        rider_beta = Rider(
            name="Beta Rider",
            pcs_slug="beta-rider",
            pcs_url="https://www.procyclingstats.com/rider/beta-rider",
        )
        event_rider_alpha = EventRider(event=event, rider=rider_alpha, team=team, price=1)
        event_rider_beta = EventRider(event=event, rider=rider_beta, team=team, price=1)
        db.session.add_all(
            [
                alpha,
                beta,
                event,
                stage_one,
                stage_two,
                team,
                rider_alpha,
                rider_beta,
                event_rider_alpha,
                event_rider_beta,
            ]
        )
        db.session.flush()
        db.session.add_all(
            [
                EventEntry(user=alpha, event=event),
                EventEntry(user=beta, event=event),
            ]
        )
        alpha_lineup = StageLineup(
            user=alpha,
            stage=stage_one,
            captain_event_rider_id=event_rider_alpha.id,
        )
        beta_lineup = StageLineup(
            user=beta,
            stage=stage_one,
            captain_event_rider_id=event_rider_beta.id,
        )
        future_lineup = StageLineup(
            user=alpha,
            stage=stage_two,
            captain_event_rider_id=event_rider_alpha.id,
        )
        db.session.add_all([alpha_lineup, beta_lineup, future_lineup])
        db.session.flush()
        alpha_lineup.riders.append(StageLineupRider(event_rider_id=event_rider_alpha.id))
        beta_lineup.riders.append(StageLineupRider(event_rider_id=event_rider_beta.id))
        future_lineup.riders.append(StageLineupRider(event_rider_id=event_rider_alpha.id))
        db.session.add_all(
            [
                StageResult(
                    stage=stage_one,
                    event_rider=event_rider_alpha,
                    rank=1,
                    status="FIN",
                ),
                StageResult(
                    stage=stage_one,
                    event_rider=event_rider_beta,
                    rank=2,
                    status="FIN",
                ),
            ]
        )
        db.session.flush()
        recalculate_stage_scores(stage_one)
        db.session.commit()
        return app, alpha.id, event.id


def login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_leaderboard_builders_include_stage_winner_leader_and_lineup():
    app, _user_id, event_id = make_leaderboard_app()
    with app.app_context():
        event = db.session.get(Event, event_id)
        total_rows = build_leaderboard(event)
        stage_rows = build_stage_leaderboard(event, event.stages[0])

        assert total_rows[0].user.username == "alpha"
        assert total_rows[0].stage_win_numbers == frozenset({1})
        assert total_rows[0].yellow_stage_numbers == frozenset({1})
        assert total_rows[0].is_yellow
        assert stage_rows[0].is_stage_winner
        assert stage_rows[0].is_yellow_after_stage
        assert stage_rows[0].score == 200
        assert stage_rows[0].lineup_riders[0].event_rider.rider.name == "Alpha Rider"
        assert stage_rows[0].lineup_riders[0].is_captain


def test_leaderboard_total_and_stage_tabs_render_expected_details():
    app, user_id, event_id = make_leaderboard_app()
    client = app.test_client()
    login(client, user_id)

    total_html = client.get(f"/events/{event_id}/leaderboard").get_data(as_text=True)
    stage_html = client.get(f"/events/{event_id}/leaderboard?stage=1").get_data(as_text=True)
    future_html = client.get(f"/events/{event_id}/leaderboard?stage=2").get_data(as_text=True)

    assert "Totaal" in total_html
    assert "Huidige leider" in total_html
    assert "Winnaar van etappe 1" in total_html
    assert "data-classification-scroll" in total_html
    assert 'aria-label="Algemeen klassement"' in total_html
    assert "scores en opstellingen per deelnemer" in stage_html
    assert "Alpha Rider" in stage_html
    assert "Beta Rider" in stage_html
    assert "Etappewinnaar" in stage_html
    assert "Leider na etappe" in stage_html
    assert "Opstelling verborgen tot de deadline" in future_html
    assert "Alpha Rider" not in future_html


def test_finished_stage_leaderboard_shows_each_users_bench():
    app, user_id, event_id = make_leaderboard_app()
    with app.app_context():
        event = db.session.get(Event, event_id)
        event.team_size = 2
        event_riders = EventRider.query.order_by(EventRider.id).all()
        for user in User.query.order_by(User.id).all():
            selection = TeamSelection(user=user, event=event, total_price=2)
            for event_rider in event_riders:
                selection.riders.append(TeamSelectionRider(event_rider=event_rider))
            db.session.add(selection)
        db.session.commit()

        rows = build_stage_leaderboard(event, event.stages[0])
        assert len(rows[0].bench_riders) == 1
        assert rows[0].bench_riders[0].event_rider.rider.name == "Beta Rider"
        assert rows[1].bench_riders[0].event_rider.rider.name == "Alpha Rider"

    client = app.test_client()
    login(client, user_id)
    html = client.get(f"/events/{event_id}/leaderboard?stage=1").get_data(as_text=True)

    assert html.count('class="leaderboard-bench"') == 2
    assert html.count('class="leaderboard-bench-card"') == 2


def test_event_overview_highlights_status_and_next_deadline():
    app, user_id, _event_id = make_leaderboard_app()
    client = app.test_client()
    login(client, user_id)

    html = client.get("/events").get_data(as_text=True)

    assert "event-card-started" in html
    assert "Volgende deadline" in html
    assert "Etappe 2 sluit" in html
    assert "data-deadline-at" in html
    assert "Ingeschreven" in html
    assert "Nog niet compleet" in html


def test_team_overview_shows_full_selections_and_rider_popularity():
    app, user_id, event_id = make_leaderboard_app()
    with app.app_context():
        event = db.session.get(Event, event_id)
        event_rider = EventRider.query.join(Rider).filter(Rider.name == "Alpha Rider").one()
        users = User.query.order_by(User.username).all()
        for user in users:
            selection = TeamSelection(user=user, event=event, total_price=1)
            selection.riders.append(TeamSelectionRider(event_rider=event_rider))
            db.session.add(selection)
        db.session.commit()

        overview = build_team_selection_overview(event)

        assert overview.participant_count == 2
        assert overview.selection_count == 2
        assert overview.completed_count == 2
        assert overview.unique_rider_count == 1
        assert overview.average_total_price == 1
        assert overview.popularity[0].event_rider.rider.name == "Alpha Rider"
        assert overview.popularity[0].selected_count == 2
        assert overview.popularity[0].percentage == 100

    client = app.test_client()
    login(client, user_id)
    response = client.get(f"/events/{event_id}/teams")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'href="/events/1/teams"' in html
    assert "Teams van deelnemers" in html
    assert "Meest gekozen renners" in html
    assert "Volledige teamselecties" in html
    assert "Alpha Rider" in html
    assert "alpha" in html
    assert "beta" in html
    assert "2 / 2" in html
    assert "100%" in html


def test_team_overview_expands_rider_popularity_beyond_top_ten():
    app, user_id, event_id = make_leaderboard_app()
    with app.app_context():
        event = db.session.get(Event, event_id)
        user = db.session.get(User, user_id)
        team = Team.query.filter_by(event_id=event_id).one()
        event_riders = [
            EventRider.query.filter_by(event_id=event_id)
            .order_by(EventRider.id)
            .first()
        ]
        for index in range(10):
            rider = Rider(
                name=f"Extra Rider {index}",
                pcs_slug=f"extra-rider-{index}",
                pcs_url=f"https://www.procyclingstats.com/rider/extra-rider-{index}",
            )
            event_rider = EventRider(event=event, rider=rider, team=team, price=1)
            db.session.add_all([rider, event_rider])
            event_riders.append(event_rider)
        db.session.flush()

        selection = TeamSelection(user=user, event=event, total_price=11)
        selection.riders.extend(
            [
                TeamSelectionRider(event_rider=event_rider)
                for event_rider in event_riders
            ]
        )
        db.session.add(selection)
        db.session.commit()

    client = app.test_client()
    login(client, user_id)
    html = client.get(f"/events/{event_id}/teams").get_data(as_text=True)

    assert "Toon alle gekozen renners" in html
    assert "11 renners" in html
    assert "Extra Rider 9" in html
