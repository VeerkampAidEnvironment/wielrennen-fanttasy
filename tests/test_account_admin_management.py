from datetime import datetime, timedelta, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from tour_femmes import create_app, db
from tour_femmes.models import (
    Award,
    Event,
    EventEntry,
    EventRider,
    Rider,
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


class TestConfig:
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    ADMIN_PASSWORD = "admin"
    PCS_BASE_URL = "https://www.procyclingstats.com"
    APP_TIMEZONE = "Europe/Amsterdam"


def make_management_app():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        user = User(
            username="demo",
            email="demo@example.com",
            password_hash=generate_password_hash("demo"),
        )
        other = User(
            username="other",
            email="other@example.com",
            password_hash=generate_password_hash("other"),
        )
        event = Event(
            name="Testkoers",
            slug="testkoers",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/testkoers/2026",
            budget=65,
            team_size=1,
            lineup_size=1,
        )
        stage = Stage(
            event=event,
            number=1,
            name="Etappe 1",
            starts_at=datetime.now(timezone.utc) - timedelta(hours=1),
            pcs_url=f"{event.pcs_url}/stage-1",
        )
        team = Team(event=event, name="Test Team")
        rider = Rider(
            name="Renner 1",
            pcs_slug="renner-1",
            pcs_url="https://www.procyclingstats.com/rider/renner-1",
        )
        event_rider = EventRider(event=event, rider=rider, team=team, price=1)
        db.session.add_all([user, other, event, stage, team, rider, event_rider])
        db.session.flush()

        selection = TeamSelection(user=user, event=event, total_price=1)
        lineup = StageLineup(user=user, stage=stage, captain_event_rider_id=event_rider.id)
        score = UserStageScore(user=user, stage=stage, score=20, captain_bonus=10)
        db.session.add_all(
            [
                EventEntry(user=user, event=event),
                EventEntry(user=other, event=event),
                selection,
                lineup,
                score,
                Award(event=event, stage=stage, user=user, award_type="stage_win"),
            ]
        )
        db.session.flush()
        selection.riders.append(TeamSelectionRider(event_rider=event_rider))
        lineup.riders.append(StageLineupRider(event_rider=event_rider))
        score.rider_scores.append(UserStageRiderScore(event_rider=event_rider, total_points=20))
        db.session.commit()
        return app, user.id, other.id, event.id


def login_user(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True
        session["_csrf_token"] = "token"


def login_admin(client):
    with client.session_transaction() as session:
        session["admin_ok"] = True
        session["_csrf_token"] = "token"


def test_account_page_updates_profile_password_and_deletes_account():
    app, user_id, _other_id, event_id = make_management_app()
    client = app.test_client()
    login_user(client, user_id)

    page = client.get("/account")
    assert page.status_code == 200
    assert "Mijn gegevens" in page.get_data(as_text=True)

    profile_response = client.post(
        "/account/profile",
        data={
            "csrf_token": "token",
            "username": "demo-renamed",
            "email": "renamed@example.com",
            "current_password": "demo",
        },
    )
    assert profile_response.status_code == 302

    password_response = client.post(
        "/account/password",
        data={
            "csrf_token": "token",
            "current_password": "demo",
            "password": "nieuw",
            "confirm": "nieuw",
        },
    )
    assert password_response.status_code == 302
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.username == "demo-renamed"
        assert user.email == "renamed@example.com"
        assert check_password_hash(user.password_hash, "nieuw")

    delete_response = client.post(
        "/account/delete",
        data={
            "csrf_token": "token",
            "current_password": "nieuw",
            "confirm_username": "demo-renamed",
        },
        follow_redirects=True,
    )
    assert delete_response.status_code == 200
    assert "Je account is verwijderd." in delete_response.get_data(as_text=True)
    with app.app_context():
        assert db.session.get(User, user_id) is None
        assert db.session.get(Event, event_id) is not None
        assert TeamSelection.query.count() == 0
        assert StageLineup.query.count() == 0
        assert UserStageScore.query.count() == 0
        assert Award.query.count() == 0


def test_admin_can_rename_and_delete_events_with_related_game_data():
    app, _user_id, _other_id, event_id = make_management_app()
    client = app.test_client()
    login_admin(client)

    rename_response = client.post(
        f"/admin/events/{event_id}/rename",
        data={"csrf_token": "token", "name": "Nieuwe Koersnaam"},
    )
    assert rename_response.status_code == 302
    with app.app_context():
        assert db.session.get(Event, event_id).name == "Nieuwe Koersnaam"

    delete_response = client.post(
        f"/admin/events/{event_id}/delete",
        data={"csrf_token": "token", "confirm_name": "Nieuwe Koersnaam"},
        follow_redirects=True,
    )
    assert delete_response.status_code == 200
    assert "Nieuwe Koersnaam" in delete_response.get_data(as_text=True)
    with app.app_context():
        assert Event.query.count() == 0
        assert Stage.query.count() == 0
        assert Team.query.count() == 0
        assert EventRider.query.count() == 0
        assert EventEntry.query.count() == 0
        assert TeamSelection.query.count() == 0
        assert StageLineup.query.count() == 0
        assert UserStageScore.query.count() == 0
        assert Award.query.count() == 0


def test_admin_users_page_deletes_user_and_keeps_event():
    app, user_id, _other_id, event_id = make_management_app()
    client = app.test_client()
    login_admin(client)

    page = client.get("/admin/users")
    assert page.status_code == 200
    assert "demo@example.com" in page.get_data(as_text=True)

    response = client.post(
        f"/admin/users/{user_id}/delete",
        data={"csrf_token": "token", "confirm_username": "demo"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Gebruiker" in html
    assert "demo" in html
    assert "is verwijderd" in html
    with app.app_context():
        assert db.session.get(User, user_id) is None
        assert db.session.get(Event, event_id) is not None
        assert EventEntry.query.count() == 1
        assert TeamSelection.query.count() == 0
        assert StageLineup.query.count() == 0
        assert UserStageScore.query.count() == 0
        assert Award.query.count() == 0


def test_admin_can_complete_an_incomplete_stage_lineup_after_deadline():
    app, _user_id, other_id, event_id = make_management_app()
    with app.app_context():
        event = db.session.get(Event, event_id)
        other = db.session.get(User, other_id)
        event_rider = EventRider.query.filter_by(event_id=event_id).one()
        selection = TeamSelection(user=other, event=event, total_price=event_rider.price)
        selection.riders.append(TeamSelectionRider(event_rider=event_rider))
        db.session.add(selection)
        db.session.commit()
        stage_id = event.stages[0].id
        event_rider_id = event_rider.id

    client = app.test_client()
    login_admin(client)

    event_page = client.get(f"/admin/events/{event_id}").get_data(as_text=True)
    assert "Selecties aanvullen" in event_page
    assert f"/admin/stages/{stage_id}/lineups" in event_page

    lineup_page = client.get(f"/admin/stages/{stage_id}/lineups")
    lineup_html = lineup_page.get_data(as_text=True)
    assert lineup_page.status_code == 200
    assert "Onvolledige selecties" in lineup_html
    assert "other" in lineup_html

    response = client.post(
        f"/admin/stages/{stage_id}/lineups/{other_id}",
        data={
            "csrf_token": "token",
            "rider_ids": str(event_rider_id),
            "captain": str(event_rider_id),
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Etappeselectie van other is aangevuld" in response.get_data(as_text=True)
    with app.app_context():
        lineup = StageLineup.query.filter_by(user_id=other_id, stage_id=stage_id).one()
        assert lineup.rider_ids() == {event_rider_id}
        assert lineup.captain_event_rider_id == event_rider_id


def test_admin_cannot_complete_stage_lineup_before_deadline():
    app, _user_id, other_id, event_id = make_management_app()
    with app.app_context():
        event = db.session.get(Event, event_id)
        event.stages[0].starts_at = datetime.now(timezone.utc) + timedelta(hours=4)
        stage_id = event.stages[0].id
        db.session.commit()

    client = app.test_client()
    login_admin(client)
    response = client.post(
        f"/admin/stages/{stage_id}/lineups/{other_id}",
        data={"csrf_token": "token"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "deadline is nog niet verstreken" in response.get_data(as_text=True)
    with app.app_context():
        assert StageLineup.query.filter_by(user_id=other_id, stage_id=stage_id).first() is None
