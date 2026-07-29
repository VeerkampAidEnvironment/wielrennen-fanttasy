from datetime import datetime, timedelta, timezone

from sqlalchemy import inspect
from werkzeug.security import generate_password_hash

from tour_femmes import create_app, db
from tour_femmes.models import (
    Event,
    EventEntry,
    EventRider,
    Rider,
    Stage,
    StageResult,
    Subleague,
    SubleagueMember,
    Team,
    User,
    UserStageScore,
)
from tour_femmes.services.deletion import delete_event_game, delete_user_account
from tour_femmes.services.game import build_leaderboard, recalculate_event_awards


class TestConfig:
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    PCS_BASE_URL = "https://www.procyclingstats.com"
    APP_TIMEZONE = "Europe/Amsterdam"


class SchemaOnlyConfig(TestConfig):
    AUTO_CREATE_SCHEMA = False


def make_subleague_app():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        alpha = User(username="alpha", password_hash=generate_password_hash("test"))
        beta = User(username="beta", password_hash=generate_password_hash("test"))
        gamma = User(username="gamma", password_hash=generate_password_hash("test"))
        viewer = User(username="viewer", password_hash=generate_password_hash("test"))
        event = Event(
            name="Test Tour",
            slug="test-tour",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/test-tour/2026",
        )
        stage_one = Stage(
            event=event,
            number=1,
            name="Etappe 1",
            starts_at=datetime.now(timezone.utc) - timedelta(days=2),
            pcs_url=f"{event.pcs_url}/stage-1",
        )
        stage_two = Stage(
            event=event,
            number=2,
            name="Etappe 2",
            starts_at=datetime.now(timezone.utc) - timedelta(days=1),
            pcs_url=f"{event.pcs_url}/stage-2",
        )
        team = Team(event=event, name="Test Team")
        rider = Rider(
            name="Test Rider",
            pcs_slug="test-rider",
            pcs_url="https://www.procyclingstats.com/rider/test-rider",
        )
        event_rider = EventRider(event=event, rider=rider, team=team, price=1)
        db.session.add_all(
            [
                alpha,
                beta,
                gamma,
                viewer,
                event,
                stage_one,
                stage_two,
                team,
                rider,
                event_rider,
            ]
        )
        db.session.flush()
        db.session.add_all(
            [
                EventEntry(user=alpha, event=event),
                EventEntry(user=beta, event=event),
                EventEntry(user=gamma, event=event),
                StageResult(stage=stage_one, event_rider=event_rider, rank=1),
                StageResult(stage=stage_two, event_rider=event_rider, rank=1),
                UserStageScore(user=alpha, stage=stage_one, score=100),
                UserStageScore(user=beta, stage=stage_one, score=80),
                UserStageScore(user=gamma, stage=stage_one, score=120),
                UserStageScore(user=alpha, stage=stage_two, score=10),
                UserStageScore(user=beta, stage=stage_two, score=90),
                UserStageScore(user=gamma, stage=stage_two, score=30),
            ]
        )
        db.session.flush()
        recalculate_event_awards(event)
        db.session.commit()
        return app, alpha.id, beta.id, gamma.id, viewer.id, event.id


def login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True
        session["_csrf_token"] = "token"


def create_league(client, event_id, name="Vriendenklassement"):
    return client.post(
        f"/events/{event_id}/subleagues/create",
        data={"csrf_token": "token", "name": name},
    )


def test_subleague_can_be_created_and_joined_by_event_participants():
    app, alpha_id, beta_id, _gamma_id, viewer_id, event_id = make_subleague_app()
    client = app.test_client()
    login(client, alpha_id)

    page = client.get(f"/events/{event_id}/subleagues")
    assert page.status_code == 200
    assert "Subcompetities" in page.get_data(as_text=True)

    response = create_league(client, event_id)
    assert response.status_code == 302
    with app.app_context():
        subleague = Subleague.query.one()
        assert subleague.owner_id == alpha_id
        assert len(subleague.join_code) == 8
        assert subleague.member_ids() == {alpha_id}
        join_code = subleague.join_code

    login(client, beta_id)
    response = client.post(
        f"/events/{event_id}/subleagues/join",
        data={"csrf_token": "token", "join_code": join_code.lower()},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Je bent toegevoegd" in response.get_data(as_text=True)
    with app.app_context():
        assert SubleagueMember.query.count() == 2

    login(client, viewer_id)
    response = client.post(
        f"/events/{event_id}/subleagues/join",
        data={"csrf_token": "token", "join_code": join_code},
        follow_redirects=True,
    )
    assert "Schrijf je eerst in" in response.get_data(as_text=True)
    with app.app_context():
        assert SubleagueMember.query.count() == 2


def test_subleague_leaderboard_filters_members_and_calculates_relative_awards():
    app, alpha_id, beta_id, gamma_id, _viewer_id, event_id = make_subleague_app()
    client = app.test_client()
    login(client, alpha_id)
    create_league(client, event_id)
    with app.app_context():
        subleague = Subleague.query.one()
        db.session.add(SubleagueMember(subleague=subleague, user_id=beta_id))
        db.session.commit()
        subleague_id = subleague.id

        event = db.session.get(Event, event_id)
        global_rows = build_leaderboard(event)
        league_rows = build_leaderboard(event, {alpha_id, beta_id})
        global_by_name = {row.user.username: row for row in global_rows}
        league_by_name = {row.user.username: row for row in league_rows}

        assert 1 in global_by_name["gamma"].stage_win_numbers
        assert 1 not in global_by_name["alpha"].stage_win_numbers
        assert league_by_name["alpha"].stage_win_numbers == frozenset({1})
        assert league_by_name["alpha"].yellow_stage_numbers == frozenset({1})
        assert league_by_name["beta"].stage_win_numbers == frozenset({2})
        assert league_by_name["beta"].is_yellow

    total_html = client.get(
        f"/events/{event_id}/leaderboard?league={subleague_id}"
    ).get_data(as_text=True)
    stage_html = client.get(
        f"/events/{event_id}/leaderboard?stage=1&league={subleague_id}"
    ).get_data(as_text=True)

    assert "Vriendenklassement" in total_html
    assert "classification-scope-options" in total_html
    assert "Algemeen" in total_html
    assert "alpha" in total_html
    assert "beta" in total_html
    assert "gamma" not in total_html
    assert "alpha" in stage_html
    assert "beta" in stage_html
    assert "gamma" not in stage_html

    login(client, gamma_id)
    assert client.get(
        f"/events/{event_id}/leaderboard?league={subleague_id}"
    ).status_code == 404


def test_members_can_leave_and_owner_can_delete_subleague():
    app, alpha_id, beta_id, _gamma_id, _viewer_id, event_id = make_subleague_app()
    client = app.test_client()
    login(client, alpha_id)
    create_league(client, event_id)
    with app.app_context():
        subleague = Subleague.query.one()
        db.session.add(SubleagueMember(subleague=subleague, user_id=beta_id))
        db.session.commit()
        subleague_id = subleague.id
        subleague_name = subleague.name

    login(client, beta_id)
    response = client.post(
        f"/events/{event_id}/subleagues/{subleague_id}/leave",
        data={"csrf_token": "token"},
    )
    assert response.status_code == 302
    with app.app_context():
        assert SubleagueMember.query.count() == 1

    login(client, alpha_id)
    response = client.post(
        f"/events/{event_id}/subleagues/{subleague_id}/delete",
        data={"csrf_token": "token", "confirm_name": subleague_name},
    )
    assert response.status_code == 302
    with app.app_context():
        assert Subleague.query.count() == 0
        assert SubleagueMember.query.count() == 0


def test_account_and_event_deletion_remove_subleague_data():
    app, alpha_id, beta_id, _gamma_id, _viewer_id, event_id = make_subleague_app()
    with app.app_context():
        event = db.session.get(Event, event_id)
        alpha = db.session.get(User, alpha_id)
        subleague = Subleague(
            event=event,
            owner=alpha,
            name="Delete test",
            join_code="DELETE23",
        )
        subleague.memberships.extend(
            [
                SubleagueMember(user=alpha),
                SubleagueMember(user_id=beta_id),
            ]
        )
        db.session.add(subleague)
        db.session.commit()

        delete_user_account(alpha)
        db.session.commit()
        assert Subleague.query.count() == 0
        assert SubleagueMember.query.count() == 0

        beta = db.session.get(User, beta_id)
        subleague = Subleague(
            event=event,
            owner=beta,
            name="Event delete test",
            join_code="EVENT234",
        )
        subleague.memberships.append(SubleagueMember(user=beta))
        db.session.add(subleague)
        db.session.commit()

        delete_event_game(event)
        db.session.commit()
        assert Subleague.query.count() == 0
        assert SubleagueMember.query.count() == 0


def test_subleague_tables_are_created_when_auto_schema_is_disabled():
    app = create_app(__name__ + ".SchemaOnlyConfig")
    with app.app_context():
        table_names = set(inspect(db.engine).get_table_names())
        assert "subleague" in table_names
        assert "subleague_member" in table_names
