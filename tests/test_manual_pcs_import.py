from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash

from tour_femmes import create_app, db
from tour_femmes.models import Event, EventRider, Rider, Stage, StageResult, Team, User


class TestConfig:
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    ADMIN_PASSWORD = "admin"
    PCS_BASE_URL = "https://www.procyclingstats.com"
    APP_TIMEZONE = "Europe/Amsterdam"


def make_manual_import_app():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        event = Event(
            name="Tour de France Femmes",
            slug="tour-de-france-femmes",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/tour-de-france-femmes/2026",
            budget=65,
            team_size=11,
            lineup_size=6,
        )
        user = User(username="demo", password_hash=generate_password_hash("demo"))
        db.session.add_all([event, user])
        db.session.commit()
        return app, event.id


def login_admin(client):
    with client.session_transaction() as session:
        session["admin_ok"] = True
        session["_csrf_token"] = "token"


def test_manual_stage_import_creates_minimal_stages_from_pasted_html():
    app, event_id = make_manual_import_app()
    client = app.test_client()
    login_admin(client)

    response = client.post(
        f"/admin/events/{event_id}/manual-stages",
        data={
            "csrf_token": "token",
            "html": """
              <a href="/race/tour-de-france-femmes/2026/stage-1">Stage 1 | Rotterdam › Rotterdam</a>
              <a href="/race/tour-de-france-femmes/2026/stage-2">Stage 2 | Dordrecht › Rotterdam</a>
            """,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        stages = Stage.query.order_by(Stage.number).all()
        assert [stage.name for stage in stages] == ["Rotterdam › Rotterdam", "Dordrecht › Rotterdam"]
        assert stages[0].live_url.endswith("/stage-1/live")


def test_manual_startlist_import_uses_existing_sporza_price_catalog():
    app, event_id = make_manual_import_app()
    client = app.test_client()
    login_admin(client)

    response = client.post(
        f"/admin/events/{event_id}/manual-startlist",
        data={
            "csrf_token": "token",
            "html": """
              <h2>Preliminary startlist</h2>
              <a href="team/fdj-suez-2026">FDJ United - SUEZ (WTW)</a>
              <a href="rider/demi-vollering">Demi Vollering</a>
            """,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        link = EventRider.query.one()
        assert link.rider.name == "Demi Vollering"
        assert link.team.name == "FDJ United - SUEZ (WTW)"
        assert link.price == 11


def test_manual_result_import_scores_pasted_stage_html():
    app, event_id = make_manual_import_app()
    client = app.test_client()
    login_admin(client)

    with app.app_context():
        event = db.session.get(Event, event_id)
        stage = Stage(
            event=event,
            number=1,
            name="Etappe 1",
            starts_at=datetime.now(timezone.utc) - timedelta(hours=1),
            pcs_url=f"{event.pcs_url}/stage-1",
        )
        team = Team(event=event, name="FDJ United - SUEZ")
        rider = Rider(
            name="Demi Vollering",
            pcs_slug="demi-vollering",
            pcs_url="https://www.procyclingstats.com/rider/demi-vollering",
        )
        link = EventRider(event=event, rider=rider, team=team, price=11)
        db.session.add_all([stage, team, rider, link])
        db.session.commit()
        stage_id = stage.id

    response = client.post(
        f"/admin/events/{event_id}/manual-stage-html",
        data={
            "csrf_token": "token",
            "stage_id": str(stage_id),
            "import_kind": "results",
            "html": """
              <table>
                <tr><th>Rnk.</th><th>Rider</th><th>Time</th></tr>
                <tr><td>1</td><td><a href="/rider/demi-vollering">Demi Vollering</a></td><td>3:12:00</td></tr>
              </table>
            """,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        result = StageResult.query.filter_by(stage_id=stage_id).one()
        assert result.rank == 1
        assert result.status == "FIN"
        assert result.base_points > 0
