from bs4 import BeautifulSoup
import pytest

from tour_femmes import create_app, db
from tour_femmes.models import Event, EventRider, Rider, Stage, StageResult, Team
from tour_femmes.services.pcs import (
    IncompleteStageResultsError,
    import_stage_results,
    parse_stage_results,
)


class TestConfig:
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    ADMIN_PASSWORD = "admin"
    PCS_BASE_URL = "https://www.procyclingstats.com"
    APP_TIMEZONE = "Europe/Amsterdam"


def make_result_app():
    app = create_app(__name__ + ".TestConfig")
    with app.app_context():
        event = Event(
            name="Testkoers",
            slug="testkoers",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/testkoers/2026",
        )
        stage = Stage(
            event=event,
            number=1,
            name="Etappe 1",
            pcs_url=f"{event.pcs_url}/stage-1",
        )
        team = Team(event=event, name="Test Team")
        links = []
        for number in range(1, 4):
            rider = Rider(
                name=f"Rider {number}",
                pcs_slug=f"rider-{number}",
                pcs_url=f"https://www.procyclingstats.com/rider/rider-{number}",
            )
            link = EventRider(event=event, rider=rider, team=team, price=1)
            db.session.add_all([rider, link])
            links.append(link)
        db.session.add_all([event, stage, team])
        db.session.commit()
        return app, stage.id, [link.id for link in links]


def result_page_html():
    return """
    <table class="results">
      <tr><th>Rnk.</th><th>GC</th><th>Timelag</th><th>Rider</th></tr>
      <tr><td>1</td><td>1</td><td>+0:00</td><td><a href="/rider/rider-1">Rider 1</a></td></tr>
      <tr><td>2</td><td>5</td><td>+0:04</td><td><a href="/rider/rider-2">Rider 2</a></td></tr>
    </table>
    <table class="points-classification">
      <tr><th>Rank</th><th>Bib</th><th>Rider</th><th>Points</th></tr>
      <tr><td>1</td><td>154</td><td><a href="/rider/rider-3">Rider 3</a></td><td>25</td></tr>
    </table>
    """


def test_stage_result_parser_ignores_other_classification_tables():
    app, stage_id, event_rider_ids = make_result_app()
    with app.app_context():
        stage = db.session.get(Stage, stage_id)
        parsed = parse_stage_results(
            BeautifulSoup(result_page_html(), "html.parser"),
            stage,
        )

    assert [(result.event_rider_id, result.rank) for result in parsed] == [
        (event_rider_ids[0], 1),
        (event_rider_ids[1], 2),
    ]


def test_stage_result_reimport_removes_obsolete_rows(monkeypatch):
    app, stage_id, event_rider_ids = make_result_app()
    soup = BeautifulSoup(result_page_html(), "html.parser")

    class FakeClient:
        def get_soup(self, _url):
            return soup

    monkeypatch.setattr("tour_femmes.services.pcs.PcsClient", FakeClient)
    monkeypatch.setattr(
        "tour_femmes.services.pcs.fetch_stage_classifications",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr("tour_femmes.services.pcs.recalculate_stage_scores", lambda _stage: None)

    with app.app_context():
        stage = db.session.get(Stage, stage_id)
        db.session.add_all(
            [
                StageResult(stage=stage, event_rider_id=event_rider_ids[0], rank=99),
                StageResult(stage=stage, event_rider_id=event_rider_ids[2], rank=1),
            ]
        )
        db.session.commit()

        assert import_stage_results(stage) == 2
        db.session.commit()
        results = StageResult.query.filter_by(stage_id=stage_id).order_by(StageResult.rank).all()

    assert [(result.event_rider_id, result.rank) for result in results] == [
        (event_rider_ids[0], 1),
        (event_rider_ids[1], 2),
    ]


def test_stage_result_import_rejects_a_partial_pcs_result(monkeypatch):
    app, stage_id, _event_rider_ids = make_result_app()
    soup = BeautifulSoup(
        """
        <table>
          <tr><th>Rnk.</th><th>GC</th><th>Timelag</th><th>Rider</th></tr>
          <tr><td>1</td><td>1</td><td>+0:00</td><td><a href="/rider/rider-1">Rider 1</a></td></tr>
        </table>
        """,
        "html.parser",
    )

    class FakeClient:
        def get_soup(self, _url):
            return soup

    monkeypatch.setattr("tour_femmes.services.pcs.PcsClient", FakeClient)

    with app.app_context():
        stage = db.session.get(Stage, stage_id)
        with pytest.raises(IncompleteStageResultsError, match="nog onvolledig"):
            import_stage_results(stage)
        assert StageResult.query.filter_by(stage_id=stage_id).count() == 0
