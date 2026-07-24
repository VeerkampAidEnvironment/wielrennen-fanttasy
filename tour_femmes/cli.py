from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import click
from flask import Flask
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import Engine
from werkzeug.security import generate_password_hash

from tour_femmes import db
from tour_femmes.models import (
    Event,
    EventEntry,
    EventRider,
    Rider,
    Stage,
    Team,
    User,
)


def register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db() -> None:
        """Maak databasetabellen aan."""
        db.create_all()
        click.echo("Database geinitialiseerd.")

    @app.cli.command("db-stats")
    def db_stats() -> None:
        """Toon aantallen per databasetabel."""
        for table in db.metadata.sorted_tables:
            count = db.session.execute(select(func.count()).select_from(table)).scalar_one()
            click.echo(f"{table.name}: {count}")

    @app.cli.command("import-sqlite")
    @click.option(
        "--source",
        type=click.Path(exists=True, dir_okay=False, path_type=Path),
        required=True,
        help="Pad naar de bestaande SQLite-database.",
    )
    @click.option("--yes", is_flag=True, help="Sla de bevestigingsvraag over.")
    def import_sqlite(source: Path, yes: bool) -> None:
        """Kopieer een bestaande SQLite-database naar de geconfigureerde database."""
        source = source.resolve()
        source_engine = create_engine(f"sqlite:///{source.as_posix()}")
        target_engine = db.engine

        if target_engine.url.get_backend_name() == "sqlite":
            target_path = target_engine.url.database
            if target_path and Path(target_path).resolve() == source:
                raise click.ClickException("Bron en doel verwijzen naar dezelfde database.")

        if not yes:
            click.confirm(
                f"Importeer {source} naar {target_engine.url.render_as_string(hide_password=True)}?",
                abort=True,
            )

        try:
            copied = copy_database(source_engine, target_engine)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        finally:
            source_engine.dispose()

        click.echo("Database-import voltooid:")
        for table_name, count in copied.items():
            click.echo(f"{table_name}: {count}")

    @app.cli.command("seed-demo")
    def seed_demo() -> None:
        """Maak een kleine lokale demokoers met renners en gebruikers."""
        db.create_all()
        if User.query.filter_by(username="demo").first():
            click.echo("Demodata bestaat al.")
            return

        user = User(username="demo", email="demo@example.com", password_hash=generate_password_hash("demo"))
        adminish = User(username="marianne", email="marianne@example.com", password_hash=generate_password_hash("demo"))
        db.session.add_all([user, adminish])

        event = Event(
            name="Demo Tour Femmes",
            slug="demo-tour-femmes",
            year=2026,
            pcs_url="https://www.procyclingstats.com/race/tour-de-france-femmes/2026",
            budget=65,
            team_size=11,
            lineup_size=6,
        )
        db.session.add(event)
        db.session.flush()

        now = datetime.now(timezone.utc)
        for number in range(1, 4):
            db.session.add(
                Stage(
                    event=event,
                    number=number,
                    name=f"Etappe {number}",
                    starts_at=now + timedelta(days=number),
                    pcs_url=f"{event.pcs_url}/stage-{number}",
                    live_url=f"{event.pcs_url}/stage-{number}/live",
                    distance_km=120 + number * 8,
                    profile_score=40 + number * 20,
                )
            )

        teams = [
            Team(event=event, name="FDJ United - SUEZ (WTW)", category="WTW"),
            Team(event=event, name="Team SD Worx - Protime (WTW)", category="WTW"),
            Team(event=event, name="Team Visma | Lease a Bike (WTW)", category="WTW"),
        ]
        db.session.add_all(teams)
        db.session.flush()

        riders = [
            ("Demi Vollering", "demi-vollering", 18, teams[0], {"GC": 5996, "Climber": 3388, "Hills": 5728}),
            ("Lotte Kopecky", "lotte-kopecky", 17, teams[1], {"Sprint": 6410, "Onedayraces": 7200}),
            ("Marianne Vos", "marianne-vos", 15, teams[2], {"Sprint": 5500, "Hills": 4400}),
            ("Pauline Ferrand-Prevot", "pauline-ferrand-prevot", 14, teams[2], {"GC": 3700, "Climber": 5100}),
            ("Elisa Longo Borghini", "elisa-longo-borghini", 13, teams[0], {"GC": 4200, "Hills": 3900}),
            ("Puck Pieterse", "puck-pieterse", 12, teams[1], {"Climber": 3200, "Hills": 4600}),
            ("Cedrine Kerbaol", "cedrine-kerbaol", 10, teams[0], {"GC": 2500, "Climber": 3400}),
            ("Niamh Fisher-Black", "niamh-fisher-black", 9, teams[1], {"Climber": 3100}),
            ("Liane Lippert", "liane-lippert", 8, teams[0], {"Hills": 3500}),
            ("Rachele Barbieri", "rachele-barbieri", 7, teams[2], {"Sprint": 3900}),
            ("Kim Le Court-Pienaar", "kim-le-court-pienaar", 6, teams[1], {"Hills": 2600}),
            ("Maeva Squiban", "maeva-squiban", 5, teams[2], {"Climber": 2100}),
        ]

        for name, slug, price, team, specialties in riders:
            rider = Rider(
                name=name,
                pcs_slug=slug,
                pcs_url=f"https://www.procyclingstats.com/rider/{slug}",
                specialties=specialties,
                best_results=["Demoresultaat"],
                grand_tour_results={},
            )
            db.session.add(rider)
            db.session.flush()
            db.session.add(EventRider(event=event, rider=rider, team=team, price=price))

        db.session.add_all([EventEntry(user=user, event=event), EventEntry(user=adminish, event=event)])
        db.session.commit()
        click.echo("Demodata aangemaakt. Log in met demo/demo.")


def copy_database(source_engine: Engine, target_engine: Engine) -> dict[str, int]:
    """Copy all application tables into an empty target database."""
    db.metadata.create_all(target_engine)

    with target_engine.connect() as target:
        non_empty = [
            table.name
            for table in db.metadata.sorted_tables
            if target.execute(select(func.count()).select_from(table)).scalar_one()
        ]
    if non_empty:
        names = ", ".join(non_empty)
        raise ValueError(f"Doeldatabase is niet leeg ({names}); import afgebroken.")

    copied: dict[str, int] = {}
    with source_engine.connect() as source, target_engine.begin() as target:
        for table in db.metadata.sorted_tables:
            rows = [dict(row) for row in source.execute(select(table)).mappings()]
            if rows:
                target.execute(table.insert(), rows)
            copied[table.name] = len(rows)
    return copied
