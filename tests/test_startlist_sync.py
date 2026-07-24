from bs4 import BeautifulSoup

from tour_femmes import create_app, db
from tour_femmes.models import Event, EventRider
from tour_femmes.services.pcs import sync_startlist


class TestConfig:
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    ADMIN_PASSWORD = "admin"
    PCS_BASE_URL = "https://www.procyclingstats.com"
    APP_TIMEZONE = "Europe/Amsterdam"


class StartlistOnlyClient:
    base_url = "https://www.procyclingstats.com"
    rate_limited = False

    def __init__(self):
        self.requested_urls = []

    def get_soup(self, url):
        self.requested_urls.append(url)
        return BeautifulSoup(
            """
            <h2>Preliminary startlist</h2>
            <a href="team/fdj-suez-2026">FDJ United - SUEZ (WTW)</a>
            <a href="rider/demi-vollering">Demi Vollering</a>
            """,
            "html.parser",
        )


def test_quick_startlist_sync_adds_new_rider_and_sporza_price_without_profile_requests():
    app = create_app(__name__ + ".TestConfig")
    client = StartlistOnlyClient()

    with app.app_context():
        event = Event(
            name="Tour de France Femmes",
            slug="tour-de-france-femmes",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/tour-de-france-femmes/2026",
        )
        db.session.add(event)
        db.session.flush()

        summary = sync_startlist(event, client=client)
        db.session.commit()

        link = EventRider.query.filter_by(event_id=event.id).one()
        assert link.rider.name == "Demi Vollering"
        assert link.price == 11
        assert summary.new_riders == ["Demi Vollering"]
        assert summary.priced_riders == ["Demi Vollering"]
        assert client.requested_urls == [
            "https://www.procyclingstats.com/race/tour-de-france-femmes/2026/startlist"
        ]
