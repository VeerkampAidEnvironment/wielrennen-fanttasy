from time import monotonic, sleep

from tour_femmes import create_app, db
from tour_femmes.admin import JOBS, JOBS_LOCK, start_admin_job
from tour_femmes.models import Event


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
        db.session.add(event)
        db.session.commit()
        return app, event.id


def login_admin(client):
    with client.session_transaction() as session:
        session["admin_ok"] = True


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
