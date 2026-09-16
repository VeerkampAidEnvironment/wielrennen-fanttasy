from datetime import datetime, timedelta, timezone

from werkzeug.datastructures import MultiDict

from bs4 import BeautifulSoup

from tour_femmes import create_app, db
from tour_femmes.models import (
    ClassificationResult,
    Event,
    EventEntry,
    EventRider,
    Rider,
    Stage,
    StageLineup,
    StageLineupRider,
    StageResult,
    StageRider,
    StageVisual,
    TeamSelection,
    TeamSelectionRider,
    User,
    UserStageScore,
)
from tour_femmes.services.game import (
    build_rider_stage_history,
    save_stage_lineup,
    unavailable_rider_statuses,
)
from tour_femmes.services.pcs import (
    enrich_missing_profiles,
    import_stage_results,
    initialize_event_from_pcs,
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


def login_admin(client):
    with client.session_transaction() as session:
        session["admin_ok"] = True
        session["_csrf_token"] = "token"


def login_user(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True
        session["_csrf_token"] = "token"


def test_admin_can_create_named_custom_race_collection():
    app = create_app(__name__ + ".TestConfig")
    client = app.test_client()
    login_admin(client)

    response = client.post(
        "/admin/",
        data=MultiDict(
            [
                ("csrf_token", "token"),
                ("event_type", "custom"),
                ("name", "Wereldkampioenschappen"),
                ("year", "2026"),
                ("budget", "80"),
                ("team_size", "8"),
                ("lineup_size", "4"),
                ("stage_name", "Wegwedstrijd vrouwen"),
                ("stage_pcs_reference", "world-championship-we"),
                ("stage_name", "Tijdrit vrouwen"),
                ("stage_pcs_reference", "world-championship-itt-we"),
                ("stage_name", "Wegwedstrijd mannen"),
                ("stage_pcs_reference", "world-championship"),
                ("stage_name", "Tijdrit mannen"),
                ("stage_pcs_reference", "world-championship-itt"),
            ]
        ),
    )

    assert response.status_code == 302
    with app.app_context():
        event = Event.query.one()
        assert event.is_custom
        assert event.name == "Wereldkampioenschappen"
        assert event.slug == "wereldkampioenschappen"
        assert event.team_size == 8
        assert event.lineup_size == 4
        assert [stage.name for stage in event.stages] == [
            "Wegwedstrijd vrouwen",
            "Tijdrit vrouwen",
            "Wegwedstrijd mannen",
            "Tijdrit mannen",
        ]
        assert event.stages[0].pcs_url.endswith("/race/world-championship-we/2026")


class CustomStartlistClient:
    base_url = "https://www.procyclingstats.com"
    rate_limited = False

    def __init__(self, pages):
        self.pages = pages
        self.requested_urls = []

    def get_soup(self, url):
        self.requested_urls.append(url)
        return BeautifulSoup(self.pages[url], "html.parser")


def startlist(team, *riders):
    rider_links = "".join(
        f'<a href="rider/{slug}">{name}</a>' for slug, name in riders
    )
    return (
        "<h2>Preliminary startlist</h2>"
        f'<a href="team/{team.casefold()}-2026">{team}</a>'
        f"{rider_links}"
    )


def test_custom_startlists_are_combined_but_lineups_remain_race_specific():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        event = Event(
            name="Wereldkampioenschappen",
            slug="wereldkampioenschappen",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/world-women/2026",
            event_type="custom",
            team_size=2,
            lineup_size=1,
        )
        women = Stage(
            event=event,
            number=1,
            name="Wegwedstrijd vrouwen",
            pcs_url="https://www.procyclingstats.com/race/world-women/2026",
        )
        men = Stage(
            event=event,
            number=2,
            name="Wegwedstrijd mannen",
            pcs_url="https://www.procyclingstats.com/race/world-men/2026",
        )
        db.session.add_all([event, women, men])
        db.session.flush()

        pages = {
            f"{women.pcs_url}/startlist": startlist(
                "Netherlands",
                ("anna-fast", "Anna Fast"),
                ("sam-shared", "Sam Shared"),
            ),
            f"{men.pcs_url}/startlist": startlist(
                "Belgium",
                ("bob-quick", "Bob Quick"),
                ("sam-shared", "Sam Shared"),
            ),
        }
        summary = sync_startlist(event, client=CustomStartlistClient(pages))
        db.session.flush()

        assert summary.seen_count == 3
        assert EventRider.query.filter_by(event_id=event.id).count() == 3
        assert {link.event_rider.rider.pcs_slug for link in women.rider_links} == {
            "anna-fast",
            "sam-shared",
        }
        assert {link.event_rider.rider.pcs_slug for link in men.rider_links} == {
            "bob-quick",
            "sam-shared",
        }

        user = User(username="player", password_hash="unused")
        db.session.add(user)
        db.session.flush()
        links = {
            link.rider.pcs_slug: link
            for link in EventRider.query.filter_by(event_id=event.id).all()
        }
        for link in links.values():
            link.price = 1
        selection = TeamSelection(user=user, event=event, total_price=0)
        selection.riders.extend(
            [
                TeamSelectionRider(event_rider=links["anna-fast"]),
                TeamSelectionRider(event_rider=links["bob-quick"]),
            ]
        )
        db.session.add_all([selection, EventEntry(user=user, event=event)])
        women.visuals.append(
            StageVisual(
                position=1,
                label="Parcoursprofiel",
                image_url="https://www.procyclingstats.com/images/profiles/women.jpg",
                image_data=b"profile",
                image_mime="image/jpeg",
            )
        )
        db.session.commit()

        assert unavailable_rider_statuses(women)[links["bob-quick"].id] == "Niet op startlijst"
        ok, message = save_stage_lineup(
            user,
            women,
            [links["bob-quick"].id],
            links["bob-quick"].id,
        )
        assert not ok
        assert "startlijst" in message
        ok, _ = save_stage_lineup(
            user,
            women,
            [links["anna-fast"].id],
            links["anna-fast"].id,
        )
        assert ok
        db.session.commit()
        event_id = event.id
        women_id = women.id
        men_id = men.id
        user_id = user.id

    client = app.test_client()
    login_user(client, user_id)
    html = client.get(f"/events/{event_id}/stages/{women_id}").get_data(as_text=True)
    assert "<h1>Wegwedstrijd vrouwen</h1>" in html
    assert "Wegwedstrijd mannen" in html
    assert "Etappe 1" not in html
    assert html.index("Opstelling voor dit onderdeel") < html.index('class="stage-profile-panel')
    stage_soup = BeautifulSoup(html, "html.parser")
    stage_cards = {
        card.select_one(".lineup-card-main strong").get_text(strip=True): card
        for card in stage_soup.select("[data-lineup-card]")
    }
    assert [badge.get_text(" ", strip=True) for badge in stage_cards["Anna Fast"].select(".rider-race-badge")] == [
        "Wegwedstrijd vrouwen"
    ]
    assert [badge.get_text(" ", strip=True) for badge in stage_cards["Bob Quick"].select(".rider-race-badge")] == [
        "Wegwedstrijd mannen"
    ]
    assert "Punten onderdelen" in stage_cards["Anna Fast"].get_text(" ", strip=True)
    assert "Tour-scores 2022-2025" not in html

    team_html = client.get(f"/events/{event_id}/team").get_data(as_text=True)
    team_soup = BeautifulSoup(team_html, "html.parser")
    participation_by_rider = {
        card["data-rider-name"]: [
            badge.get_text(" ", strip=True)
            for badge in card.select(".rider-race-badge")
        ]
        for card in team_soup.select("[data-rider-card]")
    }
    assert participation_by_rider["anna fast"] == ["Wegwedstrijd vrouwen"]
    assert participation_by_rider["bob quick"] == ["Wegwedstrijd mannen"]
    assert participation_by_rider["sam shared"] == [
        "Wegwedstrijd vrouwen",
        "Wegwedstrijd mannen",
    ]
    race_filters = team_soup.select("[data-race-filter]")
    assert [button.select_one("strong").get_text(" ", strip=True) for button in race_filters] == [
        "Alle renners",
        "Alle vrouwen",
        "Wegwedstrijd vrouwen",
        "Alle mannen",
        "Wegwedstrijd mannen",
    ]
    assert race_filters[0]["aria-pressed"] == "true"
    assert race_filters[2]["data-filter-stage-ids"] == str(women_id)
    assert race_filters[4]["data-filter-stage-ids"] == str(men_id)
    assert team_soup.select_one("[data-stage-filter], [data-gender-filter]") is None
    stage_ids_by_rider = {
        card["data-rider-name"]: card["data-stage-ids"]
        for card in team_soup.select("[data-rider-card]")
    }
    assert stage_ids_by_rider["anna fast"] == str(women_id)
    assert stage_ids_by_rider["sam shared"] == f"{women_id},{men_id}"
    genders_by_rider = {
        card["data-rider-name"]: set(filter(None, card["data-genders"].split(",")))
        for card in team_soup.select("[data-rider-card]")
    }
    assert genders_by_rider["anna fast"] == {"women"}
    assert genders_by_rider["bob quick"] == {"men"}
    assert genders_by_rider["sam shared"] == {"women", "men"}
    coverage_by_stage = {
        item["data-stage-coverage"]: {
            "count": item.select_one("[data-stage-coverage-count]").get_text(strip=True),
            "note": item.select_one("[data-stage-coverage-note]").get_text(" ", strip=True),
        }
        for item in team_soup.select("[data-stage-coverage]")
    }
    assert coverage_by_stage[str(women_id)] == {
        "count": "1",
        "note": "Maximaal 1 opstellen",
    }
    assert coverage_by_stage[str(men_id)] == {
        "count": "1",
        "note": "Maximaal 1 opstellen",
    }
    assert team_soup.select_one("[data-team-filter]") is None
    assert team_soup.select_one("[data-team-chip][aria-pressed='true']")["value"] == ""


def test_join_closes_at_the_earliest_custom_race_deadline():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        event = Event(
            name="Gesloten WK",
            slug="gesloten-wk",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/example/2026",
            event_type="custom",
        )
        later = Stage(
            event=event,
            number=1,
            name="Wegwedstrijd",
            starts_at=datetime.now(timezone.utc) + timedelta(days=1),
            pcs_url=f"{event.pcs_url}/road",
        )
        earlier = Stage(
            event=event,
            number=2,
            name="Tijdrit",
            starts_at=datetime.now(timezone.utc) - timedelta(hours=1),
            pcs_url=f"{event.pcs_url}/itt",
        )
        user = User(username="late-joiner", password_hash="unused")
        db.session.add_all([event, later, earlier, user])
        db.session.commit()
        event_id = event.id
        user_id = user.id
        assert event.team_deadline_stage().id == earlier.id

    client = app.test_client()
    login_user(client, user_id)
    overview = BeautifulSoup(client.get("/events").get_data(as_text=True), "html.parser")
    assert overview.select_one(f'form[action="/events/{event_id}/join"]') is None
    assert "Inschrijving gesloten" in overview.get_text(" ", strip=True)
    subleagues = client.get(f"/events/{event_id}/subleagues").get_data(as_text=True)
    assert ">Meedoen<" not in subleagues
    assert "inschrijven kan niet meer" in subleagues

    response = client.post(
        f"/events/{event_id}/join",
        data={"csrf_token": "token"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "De inschrijving is gesloten" in response.get_data(as_text=True)
    with app.app_context():
        assert EventEntry.query.filter_by(event_id=event_id, user_id=user_id).count() == 0


def test_custom_event_requires_at_least_two_complete_races():
    app = create_app(__name__ + ".TestConfig")
    client = app.test_client()
    login_admin(client)

    response = client.post(
        "/admin/",
        data=MultiDict(
            [
                ("csrf_token", "token"),
                ("event_type", "custom"),
                ("name", "Te klein"),
                ("year", "2026"),
                ("stage_name", "Alleen één koers"),
                ("stage_pcs_reference", "one-race"),
            ]
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Voeg minstens twee koersen toe" in response.get_data(as_text=True)
    with app.app_context():
        assert Event.query.count() == 0


def test_race_filter_offers_both_disciplines_within_each_gender():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        event = Event(
            name="Wereldkampioenschappen",
            slug="wereldkampioenschappen",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/world-championship/2026",
            event_type="custom",
            budget=75,
            team_size=1,
            lineup_size=1,
        )
        stages = [
            Stage(event=event, number=number, name=name, pcs_url=f"{event.pcs_url}/{number}")
            for number, name in enumerate(
                ("Tijdrit vrouwen", "Wegwedstrijd vrouwen", "Tijdrit mannen", "Wegwedstrijd mannen"),
                start=1,
            )
        ]
        rider = Rider(
            pcs_slug="anna-both",
            pcs_url="https://www.procyclingstats.com/rider/anna-both",
            name="Anna Both",
        )
        user = User(username="filter-player", password_hash="unused")
        event_rider = EventRider(event=event, rider=rider, price=5)
        db.session.add_all([event, *stages, event_rider, user])
        db.session.flush()
        db.session.add_all(
            [StageRider(stage=stages[0], event_rider=event_rider), StageRider(stage=stages[1], event_rider=event_rider)]
        )
        selection = TeamSelection(user=user, event=event, total_price=5)
        selection.riders.append(TeamSelectionRider(event_rider=event_rider))
        db.session.add_all([selection, EventEntry(user=user, event=event)])
        db.session.commit()
        event_id = event.id
        user_id = user.id
        women_ids = f"{stages[0].id},{stages[1].id}"
        men_ids = f"{stages[2].id},{stages[3].id}"

    client = app.test_client()
    login_user(client, user_id)
    response = client.get(f"/events/{event_id}/team")
    assert response.status_code == 200
    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    groups = soup.select(".race-filter-group")
    assert [group.select_one("h3").get_text(strip=True) for group in groups] == ["Vrouwen", "Mannen"]
    both_filters = soup.select("[data-race-filter][data-filter-match='all']")
    assert [button["data-filter-stage-ids"] for button in both_filters] == [women_ids, men_ids]
    assert [button.select_one("strong").get_text(strip=True) for button in both_filters] == [
        "Beide onderdelen", "Beide onderdelen"
    ]
    assert soup.select_one("[data-rider-card]")["data-stage-ids"] == women_ids
    assert soup.select_one("[data-team-form]")["data-budget"] == "75"


def test_custom_rider_history_uses_finished_races_even_when_numbered_later():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        event = Event(
            name="Losse koersen",
            slug="losse-koersen",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/example/2026",
            event_type="custom",
        )
        current_stage = Stage(
            event=event,
            number=1,
            name="Wegwedstrijd",
            pcs_url="https://www.procyclingstats.com/race/road/2026",
        )
        finished_stage = Stage(
            event=event,
            number=2,
            name="Tijdrit",
            pcs_url="https://www.procyclingstats.com/race/itt/2026",
        )
        rider = Rider(
            pcs_slug="test-rider",
            pcs_url="https://www.procyclingstats.com/rider/test-rider",
            name="Test Rider",
        )
        event_rider = EventRider(event=event, rider=rider, price=1)
        db.session.add_all([current_stage, finished_stage, event_rider])
        db.session.flush()
        db.session.add(StageResult(stage=finished_stage, event_rider=event_rider, rank=1, status="FIN"))
        db.session.flush()

        history = build_rider_stage_history(event, current_stage, [event_rider])[event_rider.id]

        assert [result.stage_name for result in history.results] == ["Tijdrit"]
        assert history.total_points > 0


class RaceDetailsClient:
    def __init__(self):
        self.requested_urls = []

    def get_soup(self, _url):
        self.requested_urls.append(_url)
        return BeautifulSoup(
            """
            <div>
              Date
              27 September 2026
              Start time
              12:30
              Distance
              156.4 km
              Parcours type
              Hilly
            </div>
            """,
            "html.parser",
        )


class RaceDetailsWithVisualsClient(RaceDetailsClient):
    def get_soup(self, url):
        self.requested_urls.append(url)
        if url.endswith("/info/profiles"):
            return BeautifulSoup(
                """
                <img src="images/profiles/test-profile.jpg">
                <img src="images/profiles/test-map.jpg">
                """,
                "html.parser",
            )
        return BeautifulSoup(
            "<div>Date<br>27 September 2026<br>Start time<br>09:00 (15:00 CET)</div>",
            "html.parser",
        )

    def absolute_url(self, href):
        return f"https://www.procyclingstats.com/{href}"

    def get_image(self, url):
        return url.encode(), "image/jpeg"


def test_loading_custom_race_details_twice_updates_existing_visuals():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        event = Event(
            name="Wereldkampioenschappen",
            slug="wereldkampioenschappen",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/world-women/2026",
            event_type="custom",
        )
        event.stages.extend(
            [
                Stage(number=1, name="Tijdrit vrouwen", pcs_url=event.pcs_url),
                Stage(number=2, name="Tijdrit mannen", pcs_url="https://www.procyclingstats.com/race/world-men/2026"),
            ]
        )
        db.session.add(event)
        db.session.flush()
        pcs_client = RaceDetailsWithVisualsClient()

        initialize_event_from_pcs(event, client=pcs_client)
        db.session.flush()
        first_ids = [visual.id for stage in event.stages for visual in stage.visuals]

        initialize_event_from_pcs(event, client=pcs_client)
        db.session.flush()

        assert StageVisual.query.count() == 4
        assert [visual.id for stage in event.stages for visual in stage.visuals] == first_ids
        assert all(stage.starts_at.hour == 15 for stage in event.stages)


def test_loading_custom_race_details_preserves_supplied_names_and_sets_deadlines():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        event = Event(
            name="Wereldkampioenschappen",
            slug="wereldkampioenschappen",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/world-women/2026",
            event_type="custom",
        )
        event.stages.extend(
            [
                Stage(
                    number=1,
                    name="Wegwedstrijd vrouwen",
                    pcs_url="https://www.procyclingstats.com/race/world-women/2026",
                ),
                Stage(
                    number=2,
                    name="Wegwedstrijd mannen",
                    pcs_url="https://www.procyclingstats.com/race/world-men/2026",
                ),
            ]
        )
        db.session.add(event)
        db.session.flush()

        pcs_client = RaceDetailsClient()
        count = initialize_event_from_pcs(event, client=pcs_client)
        db.session.flush()

        assert count == 2
        assert [stage.name for stage in event.stages] == [
            "Wegwedstrijd vrouwen",
            "Wegwedstrijd mannen",
        ]
        assert all(stage.starts_at is not None for stage in event.stages)
        assert all(stage.distance_km == 156.4 for stage in event.stages)
        assert pcs_client.requested_urls[::2] == [
            "https://www.procyclingstats.com/race/world-women/2026/result",
            "https://www.procyclingstats.com/race/world-men/2026/result",
        ]


class OneDayResultClient:
    def __init__(self):
        self.requested_urls = []

    def get_soup(self, url):
        self.requested_urls.append(url)
        return BeautifulSoup(
            """
            <table>
              <thead><tr><th>Rnk</th><th>Rider</th><th>Team</th><th>Pnt</th><th>Time</th></tr></thead>
              <tbody>
                <tr><td>1</td><td><a href="/rider/alex-winner">Alex Winner</a></td><td>Nation A</td><td>300</td><td>6:21:20</td></tr>
                <tr><td>2</td><td><a href="/rider/bo-runner-up">Bo Runner-up</a></td><td>Nation B</td><td>250</td><td>+1:28</td></tr>
              </tbody>
            </table>
            """,
            "html.parser",
        )


def test_custom_result_loader_uses_one_day_result_page_without_classifications():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        event = Event(
            name="Wereldkampioenschappen",
            slug="wereldkampioenschappen",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/world-championship/2026",
            event_type="custom",
            points_by_rank={"1": 60, "2": 40},
        )
        stage = Stage(
            event=event,
            number=1,
            name="Wegwedstrijd mannen",
            pcs_url="https://www.procyclingstats.com/race/world-championship/2026",
            points_by_rank={"1": 250, "2": 125},
        )
        winner = EventRider(
            event=event,
            rider=Rider(
                name="Alex Winner",
                pcs_slug="alex-winner",
                pcs_url="https://www.procyclingstats.com/rider/alex-winner",
            ),
            price=1,
        )
        runner_up = EventRider(
            event=event,
            rider=Rider(
                name="Bo Runner-up",
                pcs_slug="bo-runner-up",
                pcs_url="https://www.procyclingstats.com/rider/bo-runner-up",
            ),
            price=1,
        )
        db.session.add_all([event, stage, winner, runner_up])
        db.session.flush()
        db.session.add_all(
            [
                StageRider(stage=stage, event_rider=winner),
                StageRider(stage=stage, event_rider=runner_up),
                ClassificationResult(
                    stage=stage,
                    event_rider=winner,
                    classification="gc",
                    rank=1,
                    is_final=True,
                ),
            ]
        )
        db.session.commit()

        result_client = OneDayResultClient()
        count = import_stage_results(stage, client=result_client)
        db.session.commit()

        assert count == 2
        assert result_client.requested_urls == [f"{stage.pcs_url}/result"]
        assert ClassificationResult.query.filter_by(stage_id=stage.id).count() == 0
        results = StageResult.query.filter_by(stage_id=stage.id).order_by(StageResult.rank).all()
        assert [(result.rank, result.base_points) for result in results] == [(1, 250), (2, 125)]


def test_admin_points_can_override_one_race_and_explanation_names_each_race():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        event = Event(
            name="Wereldkampioenschappen",
            slug="wereldkampioenschappen",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/world-championship/2026",
            event_type="custom",
            team_size=1,
            lineup_size=1,
        )
        road = Stage(
            event=event,
            number=1,
            name="Wegwedstrijd vrouwen",
            pcs_url="https://www.procyclingstats.com/race/world-championship-we/2026",
        )
        time_trial = Stage(
            event=event,
            number=2,
            name="Tijdrit vrouwen",
            pcs_url="https://www.procyclingstats.com/race/world-championship-itt-we/2026",
        )
        rider = EventRider(
            event=event,
            rider=Rider(
                name="Casey Champion",
                pcs_slug="casey-champion",
                pcs_url="https://www.procyclingstats.com/rider/casey-champion",
            ),
            price=1,
        )
        user = User(username="player", password_hash="unused")
        db.session.add_all([event, road, time_trial, rider, user])
        db.session.flush()
        for stage in (road, time_trial):
            lineup = StageLineup(
                user=user,
                stage=stage,
                captain_event_rider_id=rider.id,
            )
            lineup.riders.append(StageLineupRider(event_rider=rider))
            db.session.add_all(
                [
                    lineup,
                    StageResult(stage=stage, event_rider=rider, rank=1, status="FIN"),
                ]
            )
        db.session.commit()
        event_id = event.id
        road_id = road.id
        time_trial_id = time_trial.id
        user_id = user.id

    form = MultiDict([("csrf_token", "token"), (f"stage_override_{time_trial_id}", "1")])
    for rank in range(1, 19):
        form.add(f"event_points_{rank}", "40" if rank == 1 else "0")
        form.add(f"stage_{time_trial_id}_points_{rank}", "200" if rank == 1 else "0")

    client = app.test_client()
    login_admin(client)
    response = client.post(f"/admin/events/{event_id}/points", data=form)
    assert response.status_code == 302

    with app.app_context():
        event = db.session.get(Event, event_id)
        road = db.session.get(Stage, road_id)
        time_trial = db.session.get(Stage, time_trial_id)
        assert event.points_by_rank["1"] == 40
        assert road.points_by_rank is None
        assert time_trial.points_by_rank["1"] == 200
        assert StageResult.query.filter_by(stage_id=road_id).one().base_points == 40
        assert StageResult.query.filter_by(stage_id=time_trial_id).one().base_points == 200
        assert UserStageScore.query.filter_by(stage_id=road_id).one().score == 80
        assert UserStageScore.query.filter_by(stage_id=time_trial_id).one().score == 400

    login_user(client, user_id)
    response = client.get(f"/events/{event_id}/scoring")
    assert response.status_code == 200
    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    groups = soup.select(".scoring-points-group")
    assert len(groups) == 2
    road_group = next(group for group in groups if "Wegwedstrijd vrouwen" in group.get_text(" ", strip=True))
    tt_group = next(group for group in groups if "Tijdrit vrouwen" in group.get_text(" ", strip=True))
    assert [cell.get_text(strip=True) for cell in road_group.select_one("tbody tr").select("td")] == ["#1", "40"]
    assert [cell.get_text(strip=True) for cell in tt_group.select_one("tbody tr").select("td")] == ["#1", "200"]
    assert "Losse koersen hebben geen dagelijkse of eindklassementsbonussen" in response.get_data(as_text=True)

    team_response = client.get(f"/events/{event_id}/team")
    assert team_response.status_code == 200
    assert "Alle vrouwen" not in team_response.get_data(as_text=True)
    assert "Beide onderdelen" in team_response.get_data(as_text=True)


class SparseProfileClient:
    rate_limited = False

    def __init__(self):
        self.profile_slugs = []

    def get_soup(self, url):
        if "/rider/" in url:
            self.profile_slugs.append(url.rstrip("/").rsplit("/", 1)[-1])
        return BeautifulSoup("<main><h1>PCS renner</h1></main>", "html.parser")

    def absolute_url(self, href):
        return f"https://www.procyclingstats.com/{href.lstrip('/')}"


def test_profile_enrichment_advances_past_sparse_but_successful_profiles():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        event = Event(
            name="Wereldkampioenschappen",
            slug="wereldkampioenschappen",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/world-championship/2026",
            event_type="custom",
        )
        db.session.add(event)
        for index in range(12):
            slug = f"rider-{index:02d}"
            db.session.add(
                EventRider(
                    event=event,
                    rider=Rider(
                        name=f"Rider {index:02d}",
                        pcs_slug=slug,
                        pcs_url=f"https://www.procyclingstats.com/rider/{slug}",
                    ),
                    price=1,
                )
            )
        db.session.commit()

        profile_client = SparseProfileClient()
        first = enrich_missing_profiles(
            event,
            client=profile_client,
            rider_limit=10,
            team_limit=0,
        )
        db.session.commit()
        second = enrich_missing_profiles(
            event,
            client=profile_client,
            rider_limit=10,
            team_limit=0,
        )
        db.session.commit()

        assert first.rider_details_loaded == 10
        assert first.remaining_riders == 2
        assert second.rider_details_loaded == 2
        assert second.remaining_riders == 0
        assert profile_client.profile_slugs[:10] == [f"rider-{index:02d}" for index in range(10)]
        assert profile_client.profile_slugs[10:] == ["rider-10", "rider-11"]
        assert Rider.query.filter(Rider.profile_checked_at.is_not(None)).count() == 12
