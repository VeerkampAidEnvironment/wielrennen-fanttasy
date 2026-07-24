from datetime import datetime, timezone

from tour_femmes.models import Event, Stage


def make_event() -> tuple[Event, Stage, Stage, Stage]:
    event = Event(
        name="Ronde van Polen vrouwen",
        slug="tour-de-pologne-women",
        year=2026,
        pcs_url="https://www.procyclingstats.com/race/tour-de-pologne-women/2026",
    )
    stages = [
        Stage(
            event=event,
            number=number,
            name=f"Etappe {number}",
            starts_at=datetime(2026, 7, 23 + number, hour, minute),
            pcs_url=f"{event.pcs_url}/stage-{number}",
        )
        for number, hour, minute in [(1, 13, 10), (2, 12, 30), (3, 12, 50)]
    ]
    return event, stages[0], stages[1], stages[2]


def test_only_the_stage_on_the_local_race_day_is_live():
    event, stage_one, stage_two, _stage_three = make_event()

    stage_one_prerace = datetime(2026, 7, 24, 10, 53, tzinfo=timezone.utc)
    assert event.live_stage(stage_one_prerace, "Europe/Amsterdam") is stage_one
    assert event.live_stage(stage_one_prerace, "Europe/Amsterdam") is not stage_two

    stage_two_prerace = datetime(2026, 7, 25, 8, 0, tzinfo=timezone.utc)
    assert event.live_stage(stage_two_prerace, "Europe/Amsterdam") is stage_two


def test_no_stage_is_live_before_or_after_its_local_race_day():
    event, _stage_one, _stage_two, _stage_three = make_event()

    assert event.live_stage(
        datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc),
        "Europe/Amsterdam",
    ) is None
    assert event.live_stage(
        datetime(2026, 7, 27, 12, 0, tzinfo=timezone.utc),
        "Europe/Amsterdam",
    ) is None


def test_naive_pcs_start_time_is_treated_as_local_time_for_locking():
    _event, stage_one, _stage_two, _stage_three = make_event()

    assert not stage_one.is_locked(datetime(2026, 7, 24, 11, 9, tzinfo=timezone.utc))
    assert stage_one.is_locked(datetime(2026, 7, 24, 11, 10, tzinfo=timezone.utc))
