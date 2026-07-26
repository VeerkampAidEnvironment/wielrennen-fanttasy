from datetime import datetime, timedelta, timezone
from time import monotonic, sleep

from tour_femmes import create_app, db
from tour_femmes.admin import JOBS, JOBS_LOCK, start_admin_job
from tour_femmes.models import Event, Stage


class TestConfig:
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    ADMIN_PASSWORD = "admin"
    PCS_BASE_URL = "https://www.procyclingstats.com"
    APP_TIMEZONE = "Europe/Amsterdam"


def make_admin_app():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        db.create_all()
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
            starts_at=datetime.now(timezone.utc) - timedelta(hours=1),
            pcs_url=f"{event.pcs_url}/stage-1",
        )
        db.session.add_all([event, stage])
        db.session.commit()
        return app, event.id


def login_admin(client):
    with client.session_transaction() as session:
        session["admin_ok"] = True
        session["_csrf_token"] = "token"


def test_admin_event_page_contains_loader_panel():
    app, event_id = make_admin_app()
    client = app.test_client()
    login_admin(client)

    response = client.get(f"/admin/events/{event_id}")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "data-admin-job-form" in html
    assert "data-admin-job-panel" in html
    assert "data-admin-job-count" in html
    assert "Uitslag laden" in html
    assert "/admin/stages/" in html
    assert "PCS verbinding testen" in html


def test_admin_pcs_diagnostics_route_flashes_results(monkeypatch):
    app, event_id = make_admin_app()
    client = app.test_client()
    login_admin(client)
    monkeypatch.setattr(
        "tour_femmes.admin.run_pcs_diagnostics",
        lambda _event: [{"ok": True, "message": "PCS test Koerspagina: HTTP 200"}],
    )

    response = client.post(
        f"/admin/events/{event_id}/pcs-diagnostics",
        data={"csrf_token": "token"},
        follow_redirects=True,
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "PCS test Koerspagina: HTTP 200" in html


def test_admin_job_status_reports_completed_count():
    app, _event_id = make_admin_app()
    with JOBS_LOCK:
        JOBS.clear()

    def work(progress):
        progress(2, 5, "Startlijst", "2 van 5 geladen.")
        return "Klaar."

    with app.app_context():
        job = start_admin_job("Startlijst synchroniseren", "/admin/events/1", work)

    deadline = monotonic() + 2
    while monotonic() < deadline:
        with JOBS_LOCK:
            done = JOBS[job.id].status == "done"
        if done:
            break
        sleep(0.05)

    client = app.test_client()
    login_admin(client)
    response = client.get(f"/admin/jobs/{job.id}")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["status"] == "done"
    assert payload["ok"] is True
    assert payload["current"] == 5
    assert payload["total"] == 5
    assert payload["message"] == "Klaar."


def test_admin_job_can_run_inline_for_pythonanywhere():
    app, _event_id = make_admin_app()
    app.config["INLINE_ADMIN_JOBS"] = True
    with JOBS_LOCK:
        JOBS.clear()

    with app.app_context():
        job = start_admin_job(
            "Etappes laden",
            "/admin/events/1",
            lambda progress: "Inline klaar.",
        )

    assert job.status == "done"
    assert job.ok is True
    assert job.message == "Inline klaar."
