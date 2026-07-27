from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, time
from threading import Lock
from time import monotonic, sleep
from typing import Callable
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import cloudscraper
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from flask import current_app, has_app_context

from tour_femmes import db
from tour_femmes.models import (
    ClassificationResult,
    Event,
    EventRider,
    Rider,
    Stage,
    StageResult,
    Team,
    utcnow,
)
from tour_femmes.scoring import points_for_result
from tour_femmes.services.game import recalculate_stage_scores
from tour_femmes.services.sporza_prices import load_sporza_price_catalog, sporza_edition_for_event

PCS_STAGE_RE = re.compile(r"/race/(?P<slug>[^/]+)/(?P<year>\d{4})/stage-(?P<number>\d+)")
NON_RIDER_LINK_PARTS = {"results", "program", "h2h", "more", "statistics"}
DEFAULT_PCS_REQUEST_DELAY_SECONDS = 4.0
DEFAULT_PCS_MAX_RETRIES = 2
DEFAULT_PCS_429_BACKOFF_SECONDS = 10.0
PCS_LIVE_EMBED_CACHE_SECONDS = 20.0
CLASSIFICATION_URL_SUFFIXES = {
    "gc": "gc",
    "points": "points",
    "mountains": "kom",
    "youth": "youth",
}
ProgressCallback = Callable[[int, int, str, str], None]
LIVE_EMBED_CACHE: dict[str, tuple[float, str]] = {}
LIVE_EMBED_CACHE_LOCK = Lock()
GRAND_TOUR_ALIASES = {
    "Tour de France Femmes": (
        "Tour de France Femmes",
        "Tour de France Femmes avec Zwift",
    ),
    "Giro d'Italia Women": (
        "Giro d'Italia Women",
        "Giro d'Italia Femminile",
        "Giro Donne",
        "Giro Rosa",
    ),
    "Vuelta España Femenina": (
        "Vuelta España Femenina",
        "Vuelta Espana Femenina",
        "Vuelta España Femenina by Carrefour.es",
        "Vuelta Espana Femenina by Carrefour.es",
        "Vuelta a España Femenina",
        "La Vuelta Femenina",
    ),
}
GRAND_TOUR_RIDER_IN_RACE_SLUGS = {
    "Tour de France Femmes": "tour-de-france-femmes",
    "Giro d'Italia Women": "giro-d-italia-women",
    "Vuelta España Femenina": "vuelta-espana-femenina",
}


@dataclass(frozen=True)
class ParsedTeam:
    name: str
    pcs_url: str | None = None
    category: str | None = None


@dataclass(frozen=True)
class ParsedRider:
    name: str
    pcs_slug: str
    pcs_url: str
    team_name: str
    team_url: str | None = None


@dataclass(frozen=True)
class StartlistSyncSummary:
    new_riders: list[str] = field(default_factory=list)
    restored_riders: list[str] = field(default_factory=list)
    frozen_riders: list[str] = field(default_factory=list)
    seen_count: int = 0
    priced_riders: list[str] = field(default_factory=list)
    rider_details_loaded: int = 0
    team_details_loaded: int = 0
    details_limit_reached: bool = False
    rate_limited: bool = False
    price_source: str | None = None
    price_error: str | None = None


@dataclass(frozen=True)
class ProfileEnrichmentSummary:
    rider_details_loaded: int = 0
    team_details_loaded: int = 0
    remaining_riders: int = 0
    rate_limited: bool = False


@dataclass(frozen=True)
class ParsedStage:
    number: int
    name: str
    pcs_url: str
    live_url: str
    starts_at: datetime | None = None
    distance_km: float | None = None
    profile_score: int | None = None
    vertical_meters: int | None = None
    parcours_type: str | None = None
    departure: str | None = None
    arrival: str | None = None
    profile_image_url: str | None = None


@dataclass(frozen=True)
class ParsedResult:
    event_rider_id: int
    rank: int | None
    status: str
    time_gap: str | None
    raw_result: dict[str, str]


@dataclass(frozen=True)
class LiveUpdateItem:
    posted_at: datetime
    text: str
    source_url: str | None


class PcsClient:
    """Rate-limited PCS client backed by a persistent CloudScraper session."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = 20,
        request_delay_seconds: float | None = None,
        max_retries: int | None = None,
        backoff_seconds: float | None = None,
    ) -> None:
        config = current_app.config if has_app_context() else {}
        self.base_url = (base_url or config.get("PCS_BASE_URL", "https://www.procyclingstats.com")).rstrip("/")
        self.timeout = timeout
        self.last_request_at = 0.0
        self.request_delay_seconds = float(
            request_delay_seconds
            if request_delay_seconds is not None
            else config.get("PCS_REQUEST_DELAY_SECONDS", DEFAULT_PCS_REQUEST_DELAY_SECONDS)
        )
        self.max_retries = int(
            max_retries
            if max_retries is not None
            else config.get("PCS_MAX_RETRIES", DEFAULT_PCS_MAX_RETRIES)
        )
        self.backoff_seconds = float(
            backoff_seconds
            if backoff_seconds is not None
            else config.get("PCS_429_BACKOFF_SECONDS", DEFAULT_PCS_429_BACKOFF_SECONDS)
        )
        self.rate_limited = False
        self.session: cloudscraper.CloudScraper = cloudscraper.create_scraper(
            browser=config.get("PCS_CLOUDSCRAPER_BROWSER", "chrome"),
        )
        self.session.headers.setdefault(
            "Accept-Language",
            config.get("PCS_ACCEPT_LANGUAGE", "en-US,en;q=0.9"),
        )

    def get_soup(self, url: str) -> BeautifulSoup:
        response = None
        for attempt in range(self.max_retries):
            self.wait_for_rate_limit()
            response = self.session.get(url, timeout=self.timeout)
            self.last_request_at = monotonic()
            if response.status_code == 429:
                self.rate_limited = True
                if attempt == self.max_retries - 1:
                    raise requests.HTTPError(
                        (
                            "PCS rate-limit bereikt (429). Wacht een paar minuten en probeer opnieuw; "
                            "deze app verlaagt automatisch het tempo voor volgende PCS-verzoeken."
                        ),
                        response=response,
                    )
                sleep(retry_after_seconds(response, attempt, self.backoff_seconds))
                continue

            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")

        raise RuntimeError("PCS-verzoek mislukte voordat er een reactie terugkwam.")

    def absolute_url(self, href: str) -> str:
        return urljoin(f"{self.base_url}/", href)

    def wait_for_rate_limit(self) -> None:
        elapsed = monotonic() - self.last_request_at
        if elapsed < self.request_delay_seconds:
            sleep(self.request_delay_seconds - elapsed)


def retry_after_seconds(response: requests.Response, attempt: int, base_backoff: float = DEFAULT_PCS_429_BACKOFF_SECONDS) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after and retry_after.isdigit():
        return min(float(retry_after), 180.0)
    return min(base_backoff * (attempt + 1), 180.0)


def normalize_event_reference(reference: str, year: int | None = None) -> tuple[str, int, str]:
    reference = reference.strip().strip("/")
    if not reference:
        raise ValueError("PCS-koersslug of URL is verplicht.")

    parsed = urlparse(reference)
    if parsed.netloc:
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 3 and parts[0] == "race":
            slug = parts[1]
            parsed_year = int(parts[2])
            return slug, year or parsed_year, f"https://{parsed.netloc}/race/{slug}/{year or parsed_year}"
        raise ValueError("Gebruik een PCS-koers-URL zoals https://www.procyclingstats.com/race/<slug>/<jaar>.")

    slug = reference.split("/")[0]
    if not year:
        raise ValueError("Jaar is verplicht wanneer je alleen een PCS-slug gebruikt.")
    base = current_app.config.get("PCS_BASE_URL", "https://www.procyclingstats.com").rstrip("/")
    return slug, year, f"{base}/race/{slug}/{year}"


def initialize_event_from_pcs(
    event: Event,
    client: PcsClient | None = None,
    progress: ProgressCallback | None = None,
) -> int:
    client = client or PcsClient()
    parsed_stages = parse_event_stages(client, event, progress=progress)
    for parsed in parsed_stages:
        stage = Stage.query.filter_by(event_id=event.id, number=parsed.number).first()
        if not stage:
            stage = Stage(event=event, number=parsed.number, name=parsed.name, pcs_url=parsed.pcs_url)
            db.session.add(stage)
        stage.name = parsed.name
        stage.pcs_url = parsed.pcs_url
        stage.live_url = parsed.live_url
        stage.starts_at = parsed.starts_at
        stage.distance_km = parsed.distance_km
        stage.profile_score = parsed.profile_score
        stage.vertical_meters = parsed.vertical_meters
        stage.parcours_type = parsed.parcours_type
        stage.departure = parsed.departure
        stage.arrival = parsed.arrival
        stage.profile_image_url = parsed.profile_image_url
    if progress:
        progress(len(parsed_stages), len(parsed_stages), "Etappes", "Etappes opgeslagen in de database.")
    return len(parsed_stages)


def sync_startlist(
    event: Event,
    client: PcsClient | None = None,
    progress: ProgressCallback | None = None,
) -> StartlistSyncSummary:
    """Synchronize only start-list membership, teams and available prices."""
    client = client or PcsClient()
    if progress:
        progress(0, 0, "Startlijst", "PCS startlijst ophalen.")
    soup = client.get_soup(f"{event.pcs_url}/startlist")
    parsed_riders = parse_startlist(soup, client.base_url)
    if progress:
        progress(0, len(parsed_riders), "Startlijst", f"{len(parsed_riders)} renners gevonden.")
    price_source = sporza_edition_for_event(event)
    price_catalog = None
    price_error = None
    if price_source:
        try:
            price_catalog = load_sporza_price_catalog(price_source)
        except (OSError, ValueError) as exc:
            price_error = str(exc)

    seen_slugs = {rider.pcs_slug for rider in parsed_riders}
    existing_by_slug = {
        link.rider.pcs_slug: link
        for link in EventRider.query.join(Rider).filter(EventRider.event_id == event.id).all()
    }
    riders_by_slug = {
        rider.pcs_slug: rider
        for rider in Rider.query.filter(Rider.pcs_slug.in_(seen_slugs)).all()
    }
    teams_by_name = {
        team.name: team
        for team in Team.query.filter_by(event_id=event.id).all()
    }

    new_names: list[str] = []
    restored_names: list[str] = []
    priced_names: list[str] = []

    for index, parsed in enumerate(parsed_riders, start=1):
        if progress:
            progress(index - 1, len(parsed_riders), "Startlijst", f"{parsed.name} verwerken.")
        team_name = clean_text(parsed.team_name)
        team = teams_by_name.get(team_name)
        if not team:
            team = get_or_create_team(event, team_name, parsed.team_url)
            teams_by_name[team_name] = team
        elif parsed.team_url and team.pcs_url != parsed.team_url:
            team.pcs_url = parsed.team_url

        rider = riders_by_slug.get(parsed.pcs_slug)
        if not rider:
            rider = Rider(pcs_slug=parsed.pcs_slug, pcs_url=parsed.pcs_url, name=parsed.name)
            db.session.add(rider)
            riders_by_slug[parsed.pcs_slug] = rider
            new_names.append(parsed.name)
        else:
            if rider.name != parsed.name:
                rider.name = parsed.name
            if rider.pcs_url != parsed.pcs_url:
                rider.pcs_url = parsed.pcs_url

        link = existing_by_slug.get(parsed.pcs_slug)
        if not link:
            link = EventRider(event=event, rider=rider)
            db.session.add(link)
            existing_by_slug[parsed.pcs_slug] = link
        elif link.frozen or not link.active:
            restored_names.append(parsed.name)

        if link.team is not team:
            link.team = team
        if not link.active or link.frozen or link.startlist_status != "listed":
            link.active = True
            link.frozen = False
            link.startlist_status = "listed"
        if link.price is None and price_catalog:
            price = price_catalog.price_for_rider(rider)
            if price is not None:
                link.price = price
                priced_names.append(rider.name)
        link.imported_at = utcnow()
        if progress:
            progress(index, len(parsed_riders), "Startlijst", f"{parsed.name} verwerkt.")

    frozen_names: list[str] = []
    for slug, link in existing_by_slug.items():
        if slug not in seen_slugs:
            link.active = False
            link.frozen = True
            link.startlist_status = "removed"
            frozen_names.append(link.rider.name)
    if progress:
        progress(len(parsed_riders), len(parsed_riders), "Startlijst", "Startlijst opgeslagen in de database.")

    return StartlistSyncSummary(
        new_riders=sorted(new_names),
        restored_riders=sorted(restored_names),
        frozen_riders=sorted(frozen_names),
        seen_count=len(seen_slugs),
        priced_riders=sorted(set(priced_names)),
        rate_limited=client.rate_limited,
        price_source=price_source,
        price_error=price_error,
    )


def enrich_missing_profiles(
    event: Event,
    client: PcsClient | None = None,
    rider_limit: int = 10,
    team_limit: int = 5,
    progress: ProgressCallback | None = None,
) -> ProfileEnrichmentSummary:
    """Load slow PCS profile pages separately from the quick start-list sync."""
    client = client or PcsClient()
    links = (
        EventRider.query.filter_by(event_id=event.id, active=True)
        .join(EventRider.rider)
        .order_by(EventRider.id)
        .all()
    )
    missing_links = [link for link in links if rider_profile_is_missing(link.rider)]
    batch = missing_links[:rider_limit]
    total = len(batch)
    loaded = 0
    if progress:
        progress(0, total, "Rennerprofielen", f"{len(missing_links)} profielen moeten worden aangevuld.")

    for index, link in enumerate(batch, start=1):
        if client.rate_limited:
            break
        if progress:
            progress(index - 1, total, "Rennerprofielen", f"{link.rider.name} ophalen.")
        if update_rider_details(client, link.rider):
            loaded += 1
        if progress:
            progress(index, total, "Rennerprofielen", f"{link.rider.name} verwerkt.")

    teams = list({link.team.id: link.team for link in links if link.team and not link.team.image_url}.values())
    team_loaded = 0
    for team in teams[:team_limit]:
        if client.rate_limited:
            break
        if update_team_details(client, team):
            team_loaded += 1

    remaining = max(0, len(missing_links) - loaded)
    return ProfileEnrichmentSummary(
        rider_details_loaded=loaded,
        team_details_loaded=team_loaded,
        remaining_riders=remaining,
        rate_limited=client.rate_limited,
    )


def rider_profile_is_missing(rider: Rider) -> bool:
    return not (
        rider.photo_url
        and rider.date_of_birth
        and rider.nationality
        and rider.specialties
    )


def get_or_create_team(event: Event, team_name: str, team_url: str | None = None) -> Team:
    cleaned = clean_text(team_name)
    team = Team.query.filter_by(event_id=event.id, name=cleaned).first()
    if not team:
        category_match = re.search(r"\(([^)]+)\)$", cleaned)
        category = category_match.group(1) if category_match else None
        team = Team(event=event, name=cleaned, pcs_url=team_url, category=category)
        db.session.add(team)
    elif team_url:
        team.pcs_url = team_url
    return team


def update_team_details(client: PcsClient, team: Team) -> bool:
    if not team.pcs_url:
        return False
    try:
        soup = client.get_soup(team.pcs_url)
    except requests.RequestException:
        return False

    team.image_url = parse_team_image_url(soup, client) or team.image_url
    return True


def parse_team_image_url(soup: BeautifulSoup, client: PcsClient) -> str | None:
    image = soup.find("img", src=re.compile(r"(^|/)images/shirts/", re.I))
    if image and image.get("src"):
        return client.absolute_url(image["src"])
    return None


def parse_event_stages(
    client: PcsClient,
    event: Event,
    progress: ProgressCallback | None = None,
) -> list[ParsedStage]:
    if progress:
        progress(0, 0, "Etappes", "PCS koerspagina ophalen.")
    soup = client.get_soup(event.pcs_url)
    stage_urls: dict[int, str] = {}
    for anchor in soup.find_all("a", href=True):
        absolute = client.absolute_url(anchor["href"])
        match = PCS_STAGE_RE.search(urlparse(absolute).path)
        if match:
            stage_urls[int(match.group("number"))] = absolute

    if not stage_urls:
        text = soup.get_text(" ", strip=True)
        for number, name in re.findall(r"Stage\s+(\d+)\s*\|\s*([^|]+?)(?=Stage\s+\d+|Final GC|$)", text):
            stage_number = int(number)
            stage_urls[stage_number] = f"{event.pcs_url}/stage-{stage_number}"

    total = len(stage_urls)
    if progress:
        progress(0, total, "Etappes", f"{total} etappes gevonden.")

    parsed = []
    for index, number in enumerate(sorted(stage_urls), start=1):
        if progress:
            progress(index - 1, total, "Etappes", f"Etappe {number} ophalen.")
        try:
            parsed.append(parse_stage_page(client, stage_urls[number], number))
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 429:
                parsed.append(minimal_parsed_stage(number, stage_urls[number]))
                if progress:
                    progress(index, total, "Etappes", f"PCS rate-limit bij etappe {number}; basisgegevens opgeslagen.")
                break
            raise
        if progress:
            progress(index, total, "Etappes", f"Etappe {number} geladen.")
    return parsed


def minimal_parsed_stage(number: int, stage_url: str) -> ParsedStage:
    return ParsedStage(
        number=number,
        name=f"Etappe {number}",
        pcs_url=stage_url,
        live_url=f"{stage_url}/live",
    )


def parse_stage_page(client: PcsClient, stage_url: str, number: int) -> ParsedStage:
    soup = client.get_soup(stage_url)
    text = soup.get_text("\n", strip=True)
    name = parse_stage_name(text, number)
    race_info = parse_label_values(text)
    stage_date = parse_date(race_info.get("Date"))
    stage_time = parse_time(race_info.get("Start time"))
    starts_at = None
    if stage_date:
        starts_at = datetime.combine(stage_date, stage_time or time(12, 0), tzinfo=ZoneInfo(current_app.config["APP_TIMEZONE"]))

    profile_image_url = None
    profile_heading = soup.find(string=re.compile(r"Race profile", re.I))
    if profile_heading:
        image = next((node for node in profile_heading.parent.next_elements if isinstance(node, Tag) and node.name == "img"), None)
        if image and image.get("src"):
            profile_image_url = client.absolute_url(image["src"])

    return ParsedStage(
        number=number,
        name=name,
        pcs_url=stage_url,
        live_url=f"{stage_url}/live",
        starts_at=starts_at,
        distance_km=parse_float(race_info.get("Distance")),
        profile_score=parse_int(race_info.get("ProfileScore")),
        vertical_meters=parse_int(race_info.get("Vertical meters")),
        parcours_type=race_info.get("Parcours type"),
        departure=race_info.get("Departure"),
        arrival=race_info.get("Arrival"),
        profile_image_url=profile_image_url,
    )


def parse_startlist(soup: BeautifulSoup, base_url: str) -> list[ParsedRider]:
    start_marker = soup.find(string=re.compile(r"Preliminary startlist", re.I))
    if start_marker is None:
        start_marker = soup.find(string=re.compile(r"\bStartlist\b", re.I))
    candidates = list(iter_anchors_after_marker(soup, start_marker))

    riders: list[ParsedRider] = []
    current_team: str | None = None
    current_team_url: str | None = None
    seen: set[str] = set()

    for anchor in candidates:
        href = anchor.get("href", "").strip()
        path = urlparse(urljoin(f"{base_url}/", href)).path.strip("/")
        text = clean_text(anchor.get_text(" ", strip=True)).lstrip("-*").strip()

        if not text:
            continue

        if path.startswith("team/"):
            current_team = text
            current_team_url = urljoin(f"{base_url}/", path)
            continue

        if not path.startswith("rider/") or not current_team:
            continue

        slug = path.split("/", 1)[1].strip("/")
        if not slug or slug in seen or any(part in slug for part in NON_RIDER_LINK_PARTS):
            continue

        riders.append(
            ParsedRider(
                name=text,
                pcs_slug=slug,
                pcs_url=urljoin(f"{base_url}/", path),
                team_name=current_team,
                team_url=current_team_url,
            )
        )
        seen.add(slug)

    return riders


def update_rider_details(client: PcsClient, rider: Rider) -> bool:
    try:
        soup = client.get_soup(rider.pcs_url)
    except requests.RequestException:
        return False

    text_lines = [clean_text(line) for line in soup.get_text("\n", strip=True).splitlines()]
    text_lines = [line for line in text_lines if line]

    h1 = soup.find("h1")
    if h1:
        rider.name = clean_text(h1.get_text(" ", strip=True))

    photo = soup.find("img", src=re.compile(r"riders|rider|photo", re.I)) or soup.find("img")
    if photo and photo.get("src"):
        rider.photo_url = client.absolute_url(photo["src"])

    rider.nationality = value_after_label(text_lines, "Nationality") or rider.nationality
    rider.height_m = parse_float(value_after_label(text_lines, "Height")) or rider.height_m
    rider.weight_kg = parse_float(value_after_label(text_lines, "Weight")) or rider.weight_kg
    rider.date_of_birth = parse_birth_date(text_lines) or rider.date_of_birth
    top_results = parse_top_results(soup, text_lines)
    rider.specialties = parse_specialties(text_lines)
    rider.best_results = top_results
    profile_grand_tours = parse_grand_tour_results(text_lines, top_results)
    rider.grand_tour_results = fetch_rider_grand_tour_results(client, rider, profile_grand_tours)
    rider.updated_at = utcnow()
    return True


def import_stage_results(stage: Stage) -> int:
    client = PcsClient()
    soup = client.get_soup(stage.pcs_url)
    parsed_results = parse_stage_results(soup, stage)
    for parsed in parsed_results:
        result = StageResult.query.filter_by(
            stage_id=stage.id,
            event_rider_id=parsed.event_rider_id,
        ).first()
        if not result:
            result = StageResult(stage=stage, event_rider_id=parsed.event_rider_id)
            db.session.add(result)
        result.rank = parsed.rank
        result.status = parsed.status
        result.time_gap = parsed.time_gap
        result.raw_result = parsed.raw_result
        result.base_points = points_for_result(parsed.rank, parsed.status)
        result.imported_at = utcnow()
    import_stage_classifications(stage, client)
    recalculate_stage_scores(stage)
    return len(parsed_results)


def import_stage_classifications(stage: Stage, client: PcsClient) -> int:
    links_by_slug = {
        link.rider.pcs_slug: link.id
        for link in EventRider.query.join(Rider).filter(EventRider.event_id == stage.event_id).all()
    }
    is_final = bool(stage.event.stages and stage.id == stage.event.stages[-1].id)
    imported = 0
    for classification, suffix in CLASSIFICATION_URL_SUFFIXES.items():
        url = f"{stage.pcs_url}-{suffix}"
        try:
            soup = client.get_soup(url)
        except requests.HTTPError as exc:
            # PCS responds with 500 (rather than 404) for classification tabs
            # that do not exist for a particular race. Keep classifications
            # independent so one missing jersey never rolls back valid GC data.
            if exc.response is not None and exc.response.status_code in {404, 410, 500}:
                continue
            raise
        parsed = parse_classification_results(soup, links_by_slug)
        ClassificationResult.query.filter_by(
            stage_id=stage.id,
            classification=classification,
        ).delete()
        for event_rider_id, rank in parsed:
            db.session.add(
                ClassificationResult(
                    stage=stage,
                    event_rider_id=event_rider_id,
                    classification=classification,
                    rank=rank,
                    is_final=is_final,
                    imported_at=utcnow(),
                )
            )
            imported += 1
    return imported


def parse_classification_results(
    soup: BeautifulSoup,
    links_by_slug: dict[str, int],
) -> list[tuple[int, int]]:
    candidates: list[list[tuple[int, int]]] = []
    tables = soup.find_all("table") or [soup]
    for table in tables:
        parsed: list[tuple[int, int]] = []
        seen: set[int] = set()
        for row in table.find_all("tr"):
            rider_anchor = row.find("a", href=re.compile(r"(^|/)rider/"))
            if not rider_anchor:
                continue
            cells = row.find_all(["td", "th"])
            ranks = [
                parse_rank(clean_text(cell.get_text(" ", strip=True)))
                for cell in cells[:2]
            ]
            rank = next((value for value in ranks if value), None)
            slug = urlparse(rider_anchor.get("href", "")).path.strip("/").split("rider/")[-1].strip("/")
            event_rider_id = links_by_slug.get(slug)
            if not rank or not event_rider_id or event_rider_id in seen:
                continue
            parsed.append((event_rider_id, rank))
            seen.add(event_rider_id)
        if parsed:
            candidates.append(parsed)
    return max(candidates, key=len, default=[])


def parse_stage_results(soup: BeautifulSoup, stage: Stage) -> list[ParsedResult]:
    links_by_slug = {
        link.rider.pcs_slug: link.id
        for link in EventRider.query.join(Rider).filter(EventRider.event_id == stage.event_id).all()
    }
    parsed: list[ParsedResult] = []
    seen: set[int] = set()

    for row in soup.find_all("tr"):
        cells = [clean_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["td", "th"])]
        if not cells:
            continue

        rank = parse_rank(cells[0])
        status = parse_status(cells)
        rider_anchor = row.find("a", href=re.compile(r"(^|/)rider/"))
        if not rider_anchor:
            continue

        slug = urlparse(rider_anchor["href"]).path.strip("/").split("rider/")[-1].strip("/")
        event_rider_id = links_by_slug.get(slug)
        if not event_rider_id or event_rider_id in seen:
            continue

        time_gap = next((cell for cell in cells if re.fullmatch(r"(\+)?\d+:\d{2}(:\d{2})?|\+?\d+s", cell)), None)
        parsed.append(
            ParsedResult(
                event_rider_id=event_rider_id,
                rank=rank,
                status=status,
                time_gap=time_gap,
                raw_result={"cells": " | ".join(cells)},
            )
        )
        seen.add(event_rider_id)

    return parsed


def fetch_live_updates(stage: Stage) -> list[LiveUpdateItem]:
    client = PcsClient()
    soup = client.get_soup(stage.live_url or f"{stage.pcs_url}/live")
    fetched_at = utcnow()
    return [
        LiveUpdateItem(posted_at=fetched_at, text=text, source_url=stage.live_url)
        for text in parse_live_updates(soup)
    ]


def fetch_live_embed_html(stage: Stage, force_refresh: bool = False) -> str:
    """Fetch and sanitize the real PCS LiveStats view for same-origin embedding."""
    source_url = _validated_live_url(stage.live_url or f"{stage.pcs_url}/live")
    now = monotonic()

    with LIVE_EMBED_CACHE_LOCK:
        cached = LIVE_EMBED_CACHE.get(source_url)
        if cached and not force_refresh and now - cached[0] < PCS_LIVE_EMBED_CACHE_SECONDS:
            return cached[1]

        soup = PcsClient().get_soup(source_url)
        embed_html = build_live_embed_html(soup, source_url)
        LIVE_EMBED_CACHE[source_url] = (monotonic(), embed_html)
        return embed_html


def build_live_embed_html(soup: BeautifulSoup, source_url: str) -> str:
    """Keep PCS's live dashboard, while removing scripts, forms and advertising."""
    content = soup.select_one(".page-content > div") or soup.select_one(".page-content")
    if content is None or content.select_one(".ls5b-kpi") is None:
        raise RuntimeError("PCS gaf geen herkenbare LiveStats-pagina terug.")

    fragment = BeautifulSoup(str(content), "html.parser")
    root = fragment.find()
    if root is None:
        raise RuntimeError("PCS LiveStats kon niet worden opgebouwd.")

    for node in root.select(
        "script, form, iframe, object, embed, noscript, ins, "
        ".RequestStatCont, .findBibCont, .requestStatus, .playbackCont, .detailProfileCont"
    ):
        node.decompose()

    for item in list(root.select(".timeline3 > li")):
        if clean_text(item.get_text(" ", strip=True)).lower() == "advertisement":
            item.decompose()

    pcs_base_url = _pcs_base_url(source_url)
    for tag in root.find_all(True):
        for attribute in list(tag.attrs):
            if attribute.lower().startswith("on"):
                del tag.attrs[attribute]

        if tag.name == "a":
            href = clean_text(tag.get("href", ""))
            if not href or href == "#":
                tag.name = "span"
                tag.attrs.pop("href", None)
            else:
                absolute_href = urljoin(f"{pcs_base_url}/", href)
                if _is_allowed_pcs_url(absolute_href, pcs_base_url):
                    tag["href"] = absolute_href
                    tag["target"] = "_blank"
                    tag["rel"] = "noopener noreferrer"
                else:
                    tag.name = "span"
                    tag.attrs.pop("href", None)

        if tag.name == "img" and tag.get("src"):
            absolute_src = urljoin(f"{pcs_base_url}/", tag["src"])
            if _is_allowed_pcs_url(absolute_src, pcs_base_url):
                tag["src"] = absolute_src
            else:
                tag.decompose()

    stylesheet_urls = []
    for stylesheet in soup.find_all("link", href=True):
        relations = {relation.lower() for relation in stylesheet.get("rel", [])}
        if "stylesheet" not in relations:
            continue
        absolute_url = urljoin(f"{pcs_base_url}/", stylesheet["href"])
        parsed = urlparse(absolute_url)
        if parsed.scheme == "https" and parsed.netloc.lower() in {
            urlparse(pcs_base_url).netloc.lower(),
            "code.jquery.com",
        }:
            stylesheet_urls.append(absolute_url)

    stylesheet_html = "\n".join(
        f'<link rel="stylesheet" href="{url}">' for url in dict.fromkeys(stylesheet_urls)
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="30">
  <title>PCS LiveStats</title>
  {stylesheet_html}
  <style>
    html {{ background: #fff; color-scheme: light; }}
    body {{ margin: 0; min-width: 860px; background: #fff; color: #111; }}
    .page-content {{ width: auto !important; max-width: none !important; margin: 0 !important; padding: 16px 18px 28px !important; }}
    .page-content > div {{ width: 100% !important; max-width: none !important; }}
    .bigProfile {{ max-width: none !important; }}
    .ls5b-left {{ width: calc(58% - 12px) !important; }}
    .ls5b-right {{ width: calc(42% - 12px) !important; }}
    .timeline3 .event {{ background-color: #fff; }}
    .toggleRequestStat, .toggleFindBib, .toggleCountrySelection {{ pointer-events: none; }}
    .viewKeypoints {{ pointer-events: none; }}
    @media (max-width: 900px) {{
      .page-content {{ padding: 12px !important; }}
    }}
  </style>
</head>
<body>
  <main class="page-content">{root}</main>
</body>
</html>"""


def _validated_live_url(source_url: str) -> str:
    pcs_base_url = _pcs_base_url(source_url)
    parsed = urlparse(source_url)
    if (
        parsed.scheme != "https"
        or parsed.netloc.lower() != urlparse(pcs_base_url).netloc.lower()
        or not parsed.path.lower().startswith("/race/")
        or "/live" not in parsed.path.lower()
    ):
        raise RuntimeError("Ongeldige PCS LiveStats-URL.")
    return source_url


def _pcs_base_url(source_url: str) -> str:
    configured_base = (
        current_app.config.get("PCS_BASE_URL", "https://www.procyclingstats.com")
        if has_app_context()
        else "https://www.procyclingstats.com"
    )
    configured = urlparse(configured_base)
    source = urlparse(source_url)
    if source.netloc.lower() != configured.netloc.lower():
        return configured_base.rstrip("/")
    return f"{source.scheme}://{source.netloc}".rstrip("/")


def _is_allowed_pcs_url(url: str, pcs_base_url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.netloc.lower() == urlparse(pcs_base_url).netloc.lower()


def parse_live_updates(soup: BeautifulSoup) -> list[str]:
    updates: list[str] = []
    for item in soup.find_all(["li", "p", "div"]):
        text = clean_text(item.get_text(" ", strip=True))
        if len(text) < 25 or len(text) > 600:
            continue
        if re.search(r"\b(km|attack|peloton|break|finish|gap|crash|climb|sprint|leader)\b", text, re.I):
            updates.append(text)
    deduped = list(dict.fromkeys(updates))
    return deduped[:80]


def iter_anchors_after_marker(soup: BeautifulSoup, marker: NavigableString | None) -> list[Tag]:
    if marker is None:
        return list(soup.find_all("a", href=True))

    anchors: list[Tag] = []
    for node in marker.parent.next_elements:
        if isinstance(node, NavigableString) and re.search(r"Do you know teams|back to content", str(node), re.I):
            break
        if isinstance(node, Tag) and node.name == "a" and node.get("href"):
            anchors.append(node)
    return anchors


def parse_label_values(text: str) -> dict[str, str]:
    lines = [clean_text(line).rstrip(":") for line in text.splitlines()]
    values: dict[str, str] = {}
    labels = {
        "Date",
        "Start time",
        "Distance",
        "ProfileScore",
        "Vertical meters",
        "Parcours type",
        "Departure",
        "Arrival",
    }
    for index, line in enumerate(lines[:-1]):
        if line in labels:
            value = next((candidate for candidate in lines[index + 1 : index + 5] if candidate and candidate not in labels), "")
            if value:
                values[line] = value
    return values


def parse_stage_name(text: str, number: int) -> str:
    lines = [clean_text(line) for line in text.splitlines()]
    lines = [line for line in lines if line]

    detail_marker = re.compile(rf"^\d{{4}}\s*\|\s*Stage\s+{number}(?:\s+\([^)]+\))?$", re.I)
    for index, line in enumerate(lines[:-1]):
        if detail_marker.match(line):
            candidate = lines[index + 1]
            if is_stage_route(candidate):
                return candidate

    nav_marker = re.compile(rf"^Stage\s+{number}(?:\s+\([^)]+\))?\s*\|\s*(.+)$", re.I)
    for line in lines:
        match = nav_marker.match(line)
        if match:
            return clean_text(match.group(1))

    breadcrumb_marker = re.compile(rf"^Stage\s+{number}(?:\s+\([^)]+\))?\s+\u00bb\s+(.+)$", re.I)
    for line in lines:
        match = breadcrumb_marker.match(line)
        if match and is_stage_route(match.group(1)):
            return clean_text(match.group(1))

    return f"Etappe {number}"


def is_stage_route(value: str) -> bool:
    lowered = value.lower()
    if not value or "result" in lowered or lowered.startswith("stage "):
        return False
    return not re.fullmatch(r"\(\d+(\.\d+)?\s?km\)", value, re.I)


def value_after_label(lines: list[str], label: str) -> str | None:
    label = label.rstrip(":")
    for index, line in enumerate(lines[:-1]):
        if line.rstrip(":") == label:
            return lines[index + 1]
    return None


def parse_birth_date(lines: list[str]) -> str | None:
    for index, line in enumerate(lines[:-3]):
        if line.rstrip(":") == "Date of birth":
            return " ".join(lines[index + 1 : index + 4])
    return None


def parse_specialties(lines: list[str]) -> dict[str, int]:
    candidates: dict[str, list[int]] = {}
    wanted = {"Onedayraces", "GC", "TT", "Sprint", "Climber", "Hills"}
    for index, line in enumerate(lines):
        if line in wanted and index > 0:
            value = parse_int(lines[index - 1])
            if value is not None:
                candidates.setdefault(line, []).append(value)
    return {label: max(values) for label, values in candidates.items()}


def parse_top_results(soup: BeautifulSoup | None, lines: list[str]) -> list[str]:
    if soup:
        parsed = parse_structured_top_results(soup)
        if parsed:
            return parsed

    try:
        start = lines.index("Top results") + 1
    except ValueError:
        return []
    results = []
    stop_words = {"Teams", "Program", "Key statistics"}
    pending_multiplier = ""
    for line in lines[start:]:
        if line in stop_words:
            break
        if re.fullmatch(r"\d+x|\*", line):
            pending_multiplier = "" if line == "*" else line
            continue
        if line.startswith("(") or line == "show all":
            continue
        if len(line) > 2:
            results.append(f"{pending_multiplier} {line}".strip())
            pending_multiplier = ""
        if len(results) >= 12:
            break
    return results


def parse_structured_top_results(soup: BeautifulSoup) -> list[str]:
    results = []
    for item in soup.select("ul.topresults > li"):
        multiplier = clean_text((item.select_one(".nrs") or item).get_text(" ", strip=True))
        if multiplier == "*":
            multiplier = ""

        race_box = item.select_one(".races") or item
        classification = clean_text(" ".join(span.get_text(" ", strip=True) for span in race_box.select(".blue")))
        race_link = race_box.find("a")
        race_name = clean_text(race_link.get_text(" ", strip=True)) if race_link else ""
        years = clean_text(" ".join(span.get_text(" ", strip=True) for span in race_box.select(".clr777")))

        parts = [part for part in (multiplier, classification, race_name, years) if part]
        if parts and race_name:
            results.append(" ".join(parts))
        if len(results) >= 12:
            break
    return results


def parse_grand_tour_results(lines: list[str], top_results: list[str] | None = None) -> dict[str, list[str]]:
    targets: dict[str, list[str]] = {label: [] for label in GRAND_TOUR_ALIASES}

    for result in top_results or []:
        label = grand_tour_label_for_text(result)
        if label:
            targets[label].append(result)

    years = [str(datetime.now().year - offset) for offset in range(1, 4)]
    short_years = [year[-2:] for year in years]
    for line in lines:
        label = grand_tour_label_for_text(line)
        if label and any(f"'{year}" in line or year in line for year in short_years + years):
            targets[label].append(line)

    return compact_grand_tour_results(targets)


def fetch_rider_grand_tour_results(
    client: PcsClient,
    rider: Rider,
    profile_results: dict[str, list[str]],
) -> dict[str, list[str]]:
    if not rider.pcs_slug:
        return profile_results

    targets = {label: list(profile_results.get(label, [])) for label in GRAND_TOUR_ALIASES}
    labels_to_fetch = set(GRAND_TOUR_RIDER_IN_RACE_SLUGS)
    for label in labels_to_fetch:
        race_slug = GRAND_TOUR_RIDER_IN_RACE_SLUGS.get(label)
        if not race_slug:
            continue
        try:
            stats_soup = client.get_soup(client.absolute_url(f"rider-in-race/{rider.pcs_slug}/{race_slug}"))
        except requests.RequestException:
            continue

        yearly_results = parse_rider_in_race_results(stats_soup)
        if yearly_results:
            targets[label] = yearly_results

    return compact_grand_tour_results(targets)


def parse_rider_in_race_results(soup: BeautifulSoup, limit: int | None = None) -> list[str]:
    for table in soup.find_all("table"):
        headers = [clean_text(cell.get_text(" ", strip=True)) for cell in table.find_all("th")]
        if not {"Year", "Result", "Stage wins"}.issubset(headers):
            continue

        results: list[str] = []
        for row in table.find_all("tr"):
            cells = [clean_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["td", "th"])]
            if len(cells) < 5 or not re.fullmatch(r"\d{4}", cells[0]):
                continue

            result = format_rider_in_race_result(cells)
            if result:
                results.append(result)
            if limit is not None and len(results) >= limit:
                break
        return results

    return []


def format_rider_in_race_result(cells: list[str]) -> str | None:
    year, gc_result, stage_wins, stage_top10s = cells[:4]
    parts: list[str] = []
    if gc_result and gc_result != "-":
        upper_result = gc_result.upper()
        parts.append(upper_result if upper_result in {"DNF", "DNS", "DSQ", "OTL", "DF", "NR"} else f"GC {gc_result}")
    if stage_wins and stage_wins not in {"-", "0"}:
        parts.append(f"{stage_wins} stage win{'s' if stage_wins != '1' else ''}")
    if stage_top10s and stage_top10s not in {"-", "0"}:
        parts.append(f"{stage_top10s} top-10{'s' if stage_top10s != '1' else ''}")
    return f"{year}: {', '.join(parts)}" if parts else None


def grand_tour_label_for_text(value: str) -> str | None:
    folded = value.casefold()
    for label, aliases in GRAND_TOUR_ALIASES.items():
        if any(alias.casefold() in folded for alias in aliases):
            return label
    return None


def compact_grand_tour_results(targets: dict[str, list[str]]) -> dict[str, list[str]]:
    return {key: list(dict.fromkeys(value)) for key, value in targets.items() if value}


def parse_date(value: str | None) -> date | None:
    if not value or value == "-":
        return None
    value = re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", r"\1", clean_text(value), flags=re.I)
    for fmt in ("%d %B %Y", "%d %b %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_time(value: str | None) -> time | None:
    if not value or value == "-":
        return None
    match = re.search(r"(\d{1,2}):(\d{2})", value)
    if not match:
        return None
    return time(int(match.group(1)), int(match.group(2)))


def parse_float(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"\d+([.,]\d+)?", value)
    if not match:
        return None
    return float(match.group(0).replace(",", "."))


def parse_int(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"\d+", value.replace(" ", ""))
    if not match:
        return None
    return int(match.group(0))


def parse_rank(value: str) -> int | None:
    match = re.match(r"#?(\d+)$", value.strip())
    return int(match.group(1)) if match else None


def parse_status(cells: list[str]) -> str:
    for cell in cells:
        upper = cell.upper()
        if upper in {"DNF", "DNS", "DSQ", "OTL", "DF", "NR"}:
            return upper
    return "FIN"


def clean_text(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", value).strip()
