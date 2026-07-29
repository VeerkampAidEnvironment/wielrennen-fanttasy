from bs4 import BeautifulSoup
import requests

from tour_femmes import create_app, db
from tour_femmes.models import ClassificationResult, Event, EventRider, Rider, Stage, Team
from tour_femmes.services.pcs import (
    import_stage_classifications,
    sync_event_images,
    sync_startlist,
)


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


class PartiallyAvailableClassificationClient:
    def get_soup(self, url):
        if url.endswith("-gc"):
            return BeautifulSoup(
                """
                <table>
                  <tr><th>Rnk.</th><th>Rider</th></tr>
                  <tr><td>1</td><td><a href="/rider/demi-vollering">Demi Vollering</a></td></tr>
                </table>
                """,
                "html.parser",
            )
        response = requests.Response()
        response.status_code = 500
        response.url = url
        raise requests.HTTPError("classification unavailable", response=response)


class ImageOnlyClient:
    rate_limited = False
    base_url = "https://www.procyclingstats.com"

    def __init__(self):
        self.requested_urls = []
        self.profile_urls = []

    def get_soup(self, url):
        self.profile_urls.append(url)
        return BeautifulSoup(
            '<img src="images/riders/unknown.jpg">',
            "html.parser",
        )

    def absolute_url(self, href):
        return f"{self.base_url}/{href.lstrip('/')}"

    def get_image(self, url):
        self.requested_urls.append(url)
        mime = "image/png" if "shirts" in url else "image/jpeg"
        return url.encode(), mime


def test_image_sync_stores_rider_and_team_images_without_loading_profile_statistics():
    app = create_app(__name__ + ".TestConfig")
    client = ImageOnlyClient()

    with app.app_context():
        event = Event(
            name="Tour de France Femmes",
            slug="tour-de-france-femmes",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/tour-de-france-femmes/2026",
        )
        team = Team(
            event=event,
            name="FDJ United - SUEZ",
            image_url="https://www.procyclingstats.com/images/shirts/fdj.png",
        )
        rider = Rider(
            name="Demi Vollering",
            pcs_slug="demi-vollering",
            pcs_url="https://www.procyclingstats.com/rider/demi-vollering",
            photo_url="https://www.procyclingstats.com/images/riders/demi.jpg",
        )
        rider_without_url = Rider(
            name="Nieuwe Renner",
            pcs_slug="nieuwe-renner",
            pcs_url="https://www.procyclingstats.com/rider/nieuwe-renner",
        )
        link = EventRider(event=event, rider=rider, team=team, price=11)
        second_link = EventRider(event=event, rider=rider_without_url, team=team, price=5)
        db.session.add_all([event, team, rider, rider_without_url, link, second_link])
        db.session.flush()

        summary = sync_event_images(event, client=client)
        db.session.flush()

        assert rider.photo_data == rider.photo_url.encode()
        assert rider.photo_mime == "image/jpeg"
        assert rider_without_url.photo_url.endswith("/images/riders/unknown.jpg")
        assert rider_without_url.photo_data == rider_without_url.photo_url.encode()
        assert team.image_data == team.image_url.encode()
        assert team.image_mime == "image/png"
        assert summary.rider_images_loaded == 2
        assert summary.team_images_loaded == 1
        assert summary.remaining_images == 0
        assert client.profile_urls == [rider_without_url.pcs_url]
        assert client.requested_urls == [
            rider.photo_url,
            rider_without_url.photo_url,
            team.image_url,
        ]


def test_missing_classification_tabs_do_not_rollback_available_gc():
    app = create_app(__name__ + ".TestConfig")

    with app.app_context():
        event = Event(
            name="Tour de Pologne Women",
            slug="tour-de-pologne-women",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/tour-de-pologne-women/2026",
        )
        stage = Stage(
            event=event,
            number=1,
            name="Stage 1",
            pcs_url=f"{event.pcs_url}/stage-1",
        )
        team = Team(event=event, name="FDJ United - SUEZ")
        rider = Rider(
            name="Demi Vollering",
            pcs_slug="demi-vollering",
            pcs_url="https://www.procyclingstats.com/rider/demi-vollering",
        )
        link = EventRider(event=event, rider=rider, team=team, price=11)
        db.session.add_all([event, stage, team, rider, link])
        db.session.flush()

        imported = import_stage_classifications(
            stage,
            PartiallyAvailableClassificationClient(),
        )
        db.session.flush()

        assert imported == 1
        result = ClassificationResult.query.filter_by(stage_id=stage.id).one()
        assert result.classification == "gc"
        assert result.rank == 1
