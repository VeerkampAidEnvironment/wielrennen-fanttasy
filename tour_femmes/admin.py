from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import wraps
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock, Thread
from time import monotonic
from uuid import uuid4

import requests
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, logout_user

from tour_femmes import db
from tour_femmes.models import Event, EventRider, Stage, User
from tour_femmes.services.deletion import delete_event_game, delete_user_account
from tour_femmes.services.pcs import (
    PcsClient,
    enrich_missing_profiles,
    import_stage_results,
    initialize_event_from_pcs,
    normalize_event_reference,
    sync_startlist,
)
from tour_femmes.services.pcs_database_import import (
    PcsDatabaseImportError,
    import_pcs_database,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@dataclass
class AdminJob:
    id: str
    title: str
    status: str
    current: int
    total: int
    label: str
    message: str
    redirect_url: str
    ok: bool | None = None


JOBS: dict[str, AdminJob] = {}
JOBS_LOCK = Lock()


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_ok"):
            return redirect(url_for("admin.login", next=request.full_path))
        return view(*args, **kwargs)

    return wrapped


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == current_app.config["ADMIN_PASSWORD"]:
            session["admin_ok"] = True
            flash("Admintoegang geactiveerd.", "success")
            return redirect(request.args.get("next") or url_for("admin.dashboard"))
        flash("Onjuist adminwachtwoord.", "danger")
    return render_template("admin/login.html")


@admin_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("admin_ok", None)
    flash("Admintoegang uitgeschakeld.", "info")
    return redirect(url_for("auth.login"))


@admin_bp.route("/", methods=["GET", "POST"])
@admin_required
def dashboard():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        reference = request.form.get("pcs_reference", "").strip()
        year_raw = request.form.get("year", "").strip()
        budget = _int_or_default(request.form.get("budget"), 65)
        team_size = _int_or_default(request.form.get("team_size"), 11)
        lineup_size = 6

        if not name:
            flash("Koersnaam is verplicht.", "danger")
            return redirect(url_for("admin.dashboard"))

        try:
            slug, year, pcs_url = normalize_event_reference(reference, int(year_raw) if year_raw else None)
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("admin.dashboard"))

        event = Event.query.filter_by(slug=slug, year=year).first()
        if event:
            flash("Die koers bestaat al.", "warning")
            return redirect(url_for("admin.event_detail", event_id=event.id))

        event = Event(
            name=name,
            slug=slug,
            year=year,
            pcs_url=pcs_url,
            budget=budget,
            team_size=team_size,
            lineup_size=lineup_size,
        )
        db.session.add(event)
        db.session.commit()
        flash("Koers aangemaakt. Laad nu de etappes.", "success")
        return redirect(url_for("admin.event_detail", event_id=event.id))

    events = Event.query.order_by(Event.created_at.desc()).all()
    return render_template("admin/dashboard.html", events=events, user_count=User.query.count())


@admin_bp.route("/import-pcs-database", methods=["POST"])
@admin_required
def import_pcs_database_upload():
    if _direct_pcs_imports_enabled():
        flash(
            "Database-upload is alleen bedoeld voor de online omgeving. "
            "Werk PCS-gegevens hier lokaal rechtstreeks bij.",
            "warning",
        )
        return redirect(url_for("admin.dashboard"))

    if request.form.get("confirm_pcs_only") != "1":
        flash("Bevestig eerst dat alleen koersdata wordt geïmporteerd.", "warning")
        return redirect(url_for("admin.dashboard"))

    upload = request.files.get("database")
    if not upload or not upload.filename:
        flash("Kies de lokale SQLite-database om te uploaden.", "danger")
        return redirect(url_for("admin.dashboard"))

    max_bytes = int(current_app.config.get("PCS_DATABASE_UPLOAD_MAX_BYTES", 64 * 1024 * 1024))
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(prefix="pcs-import-", suffix=".sqlite3", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            total_bytes = 0
            while chunk := upload.stream.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise PcsDatabaseImportError(
                        f"Het databasebestand is groter dan de limiet van {max_bytes // (1024 * 1024)} MB."
                    )
                temporary.write(chunk)

        report = import_pcs_database(temporary_path)
        db.session.commit()
        flash(
            "Lokale koersdata veilig geïmporteerd. " + report.summary()
            + " Gebruikers, deelnames, teamselecties en etappeselecties zijn niet ingelezen of overschreven.",
            "success",
        )
    except PcsDatabaseImportError as exc:
        db.session.rollback()
        flash(f"Database-import geweigerd: {exc}", "danger")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Import van lokale PCS-database mislukt")
        flash(
            "Database-import mislukt. Er is niets opgeslagen; controleer de serverlog voor details.",
            "danger",
        )
    finally:
        if temporary_path:
            temporary_path.unlink(missing_ok=True)
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/events/<int:event_id>/rename", methods=["POST"])
@admin_required
def rename_event(event_id: int):
    event = Event.query.get_or_404(event_id)
    name = request.form.get("name", "").strip()
    if not name:
        flash("Koersnaam is verplicht.", "danger")
        return redirect(request.referrer or url_for("admin.dashboard"))

    event.name = name
    db.session.commit()
    flash("Koersnaam opgeslagen.", "success")
    return redirect(request.referrer or url_for("admin.event_detail", event_id=event.id))


@admin_bp.route("/events/<int:event_id>/delete", methods=["POST"])
@admin_required
def delete_event(event_id: int):
    event = Event.query.get_or_404(event_id)
    confirmation = request.form.get("confirm_name", "").strip()
    if confirmation not in {event.name, event.slug}:
        flash("Typ de koersnaam exact over om deze koers te verwijderen.", "danger")
        return redirect(request.referrer or url_for("admin.dashboard"))

    event_name = event.name
    delete_event_game(event)
    db.session.commit()
    flash(f"Koers '{event_name}' is verwijderd.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/users")
@admin_required
def users():
    users = User.query.order_by(User.username).all()
    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id: int):
    user = User.query.get_or_404(user_id)
    confirmation = request.form.get("confirm_username", "").strip()
    if confirmation != user.username:
        flash("Typ de gebruikersnaam exact over om deze gebruiker te verwijderen.", "danger")
        return redirect(url_for("admin.users"))

    username = user.username
    if current_user.is_authenticated and current_user.id == user.id:
        logout_user()
    delete_user_account(user)
    db.session.commit()
    flash(f"Gebruiker '{username}' is verwijderd.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/events/<int:event_id>")
@admin_required
def event_detail(event_id: int):
    event = Event.query.get_or_404(event_id)
    missing_prices = (
        EventRider.query.filter_by(event_id=event.id, active=True)
        .filter(EventRider.price.is_(None))
        .join(EventRider.rider)
        .order_by(EventRider.id)
        .all()
    )
    active_count = EventRider.query.filter_by(event_id=event.id, active=True).count()
    frozen_count = EventRider.query.filter_by(event_id=event.id, frozen=True).count()
    return render_template(
        "admin/event.html",
        event=event,
        missing_prices=missing_prices,
        active_count=active_count,
        frozen_count=frozen_count,
    )


@admin_bp.route("/events/<int:event_id>/initialize", methods=["POST"])
@admin_required
def initialize_event(event_id: int):
    event = Event.query.get_or_404(event_id)
    if blocked := _direct_pcs_blocked_response(event):
        return blocked
    if _wants_json():
        job = start_admin_job(
            title="Etappes laden uit PCS",
            redirect_url=url_for("admin.event_detail", event_id=event.id),
            work=lambda progress: initialize_event_job(event.id, progress),
        )
        return jsonify(asdict(job))

    try:
        count = initialize_event_from_pcs(event, client=interactive_pcs_client())
        db.session.commit()
        flash(f"{count} etappes geladen uit PCS.", "success")
    except requests.RequestException as exc:
        db.session.rollback()
        flash(f"PCS-verzoek mislukt: {exc}", "danger")
    return redirect(url_for("admin.event_detail", event_id=event.id))


@admin_bp.route("/events/<int:event_id>/sync-startlist", methods=["POST"])
@admin_required
def sync_event_startlist(event_id: int):
    event = Event.query.get_or_404(event_id)
    if blocked := _direct_pcs_blocked_response(event):
        return blocked
    if _wants_json():
        job = start_admin_job(
            title="Startlijst synchroniseren",
            redirect_url=url_for("admin.event_detail", event_id=event.id),
            work=lambda progress: sync_startlist_job(event.id, progress),
        )
        return jsonify(asdict(job))

    try:
        summary = sync_startlist(
            event,
            client=interactive_pcs_client(),
        )
        db.session.commit()
        flash(
            (
                f"Startlijst gesynchroniseerd: {summary.seen_count} renners gezien, "
                f"{len(summary.new_riders)} nieuw, {len(summary.restored_riders)} teruggezet, "
                f"{len(summary.frozen_riders)} bevroren, "
                f"{len(summary.priced_riders)} automatisch geprijsd."
            ),
            "success",
        )
        if summary.new_riders:
            flash("Nieuwe renners: " + ", ".join(summary.new_riders[:30]), "info")
        if summary.price_source and summary.priced_riders:
            flash(f"Prijzen geladen uit Sporza {summary.price_source}.", "success")
        if summary.price_error:
            flash(f"Sporza-prijzen konden niet worden geladen: {summary.price_error}", "warning")
        if summary.frozen_riders:
            flash("Bevroren: " + ", ".join(summary.frozen_riders[:30]), "warning")
    except requests.RequestException as exc:
        db.session.rollback()
        flash(f"PCS-verzoek mislukt: {exc}", "danger")
    return redirect(url_for("admin.event_detail", event_id=event.id))


@admin_bp.route("/events/<int:event_id>/enrich-profiles", methods=["POST"])
@admin_required
def enrich_event_profiles(event_id: int):
    event = Event.query.get_or_404(event_id)
    if blocked := _direct_pcs_blocked_response(event):
        return blocked
    if _wants_json():
        job = start_admin_job(
            title="Ontbrekende rennerprofielen ophalen",
            redirect_url=url_for("admin.event_detail", event_id=event.id),
            work=lambda progress: enrich_profiles_job(event.id, progress),
        )
        return jsonify(asdict(job))

    try:
        summary = enrich_missing_profiles(event, client=interactive_pcs_client())
        db.session.commit()
        flash(
            f"{summary.rider_details_loaded} profielen en {summary.team_details_loaded} ploegafbeeldingen bijgewerkt. "
            f"{summary.remaining_riders} profielen resterend.",
            "success",
        )
    except requests.RequestException as exc:
        db.session.rollback()
        flash(f"PCS-profielimport mislukt: {exc}", "danger")
    return redirect(url_for("admin.event_detail", event_id=event.id))


@admin_bp.route("/events/<int:event_id>/pcs-diagnostics", methods=["POST"])
@admin_required
def pcs_diagnostics(event_id: int):
    event = Event.query.get_or_404(event_id)
    if blocked := _direct_pcs_blocked_response(event):
        return blocked
    results = run_pcs_diagnostics(event)
    ok = all(result["ok"] for result in results)
    for result in results:
        flash(result["message"], "success" if result["ok"] else "warning")
    if not ok:
        flash("Controleer de PythonAnywhere errorlog voor de volledige PCS-foutmelding.", "warning")
    return redirect(url_for("admin.event_detail", event_id=event.id))


@admin_bp.route("/jobs/<job_id>")
@admin_required
def job_status(job_id: str):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return jsonify({"ok": False, "message": "Job niet gevonden."}), 404
        return jsonify(asdict(job))


@admin_bp.route("/events/<int:event_id>/prices", methods=["GET", "POST"])
@admin_required
def prices(event_id: int):
    event = Event.query.get_or_404(event_id)
    riders = (
        EventRider.query.filter_by(event_id=event.id)
        .join(EventRider.rider)
        .order_by(EventRider.active.desc(), EventRider.price.is_(None).desc(), EventRider.id)
        .all()
    )

    if request.method == "POST":
        for event_rider in riders:
            price_raw = request.form.get(f"price_{event_rider.id}", "").strip()
            if price_raw == "":
                event_rider.price = None
                continue
            try:
                event_rider.price = max(0, int(price_raw))
            except ValueError:
                flash(f"Ongeldige prijs voor {event_rider.rider.name}.", "danger")
                return redirect(url_for("admin.prices", event_id=event.id))
        db.session.commit()
        flash("Prijzen opgeslagen.", "success")
        return redirect(url_for("admin.event_detail", event_id=event.id))

    return render_template("admin/prices.html", event=event, riders=riders)


@admin_bp.route("/stages/<int:stage_id>/import-results", methods=["POST"])
@admin_required
def import_results(stage_id: int):
    stage = Stage.query.get_or_404(stage_id)
    if blocked := _direct_pcs_blocked_response(stage.event, stage):
        return blocked
    if not stage.is_locked():
        flash("Een uitslag kan pas worden geladen nadat de etappe is gestart.", "warning")
        return redirect(url_for("events.stage", event_id=stage.event_id, stage_id=stage.id))
    try:
        count = import_stage_results(stage)
        db.session.commit()
        flash(f"{count} uitslagregels geladen en scores herberekend.", "success")
    except requests.RequestException as exc:
        db.session.rollback()
        flash(f"PCS-uitslagimport mislukt: {exc}", "danger")
    return redirect(url_for("events.stage", event_id=stage.event_id, stage_id=stage.id))


def _int_or_default(value: str | None, default: int) -> int:
    try:
        return int(value or default)
    except ValueError:
        return default


def run_pcs_diagnostics(event: Event) -> list[dict[str, object]]:
    urls = [
        ("Koerspagina", event.pcs_url),
        ("Startlijst", f"{event.pcs_url}/startlist"),
    ]
    first_stage = event.first_stage()
    if first_stage and first_stage.profile_image_url:
        urls.append(("Afbeelding", first_stage.profile_image_url))

    client = PcsClient(timeout=8, request_delay_seconds=0, max_retries=1, backoff_seconds=0)
    results: list[dict[str, object]] = []
    for label, url in urls:
        canonical_url = client.canonical_url(url)
        started_at = monotonic()
        try:
            response = client.session.get(canonical_url, timeout=8, stream=True)
            elapsed = monotonic() - started_at
            content_type = response.headers.get("Content-Type", "onbekend").split(";")[0]
            ok = 200 <= response.status_code < 400
            response.close()
            results.append(
                {
                    "ok": ok,
                    "message": (
                        f"PCS test {label}: HTTP {response.status_code}, "
                        f"{content_type}, {elapsed:.1f}s, {canonical_url}"
                    ),
                }
            )
        except requests.RequestException as exc:
            current_app.logger.warning("PCS diagnostics failed for %s %s: %s", label, canonical_url, exc)
            results.append(
                {
                    "ok": False,
                    "message": f"PCS test {label}: fout na {monotonic() - started_at:.1f}s, {short_error(exc)}",
                }
            )
    return results


def short_error(exc: Exception, limit: int = 180) -> str:
    text = str(exc).replace("\n", " ")
    return text if len(text) <= limit else f"{text[:limit - 1]}..."


def start_admin_job(title: str, redirect_url: str, work) -> AdminJob:
    job = AdminJob(
        id=uuid4().hex,
        title=title,
        status="queued",
        current=0,
        total=0,
        label=title,
        message="Wachten om te starten.",
        redirect_url=redirect_url,
    )
    app = current_app._get_current_object()
    with JOBS_LOCK:
        JOBS[job.id] = job

    if current_app.config.get("INLINE_ADMIN_JOBS", False):
        # PythonAnywhere does not support background threads in web workers.
        # Running inline keeps these infrequent admin imports reliable there.
        run_admin_job(app, job.id, work)
    else:
        thread = Thread(target=run_admin_job, args=(app, job.id, work), daemon=True)
        thread.start()
    return job


def run_admin_job(app, job_id: str, work) -> None:
    with app.app_context():
        update_admin_job(job_id, status="running", message="Gestart.")
        try:
            message = work(lambda current, total, label, detail: update_admin_job(
                job_id,
                current=current,
                total=total,
                label=label,
                message=detail,
            ))
            db.session.commit()
            with JOBS_LOCK:
                job = JOBS[job_id]
                job.status = "done"
                job.ok = True
                job.message = message
                if job.total and job.current < job.total:
                    job.current = job.total
        except Exception as exc:
            db.session.rollback()
            with JOBS_LOCK:
                job = JOBS[job_id]
                job.status = "done"
                job.ok = False
                job.message = f"PCS-verzoek mislukt: {exc}"
        finally:
            db.session.remove()


def update_admin_job(job_id: str, **changes) -> None:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return
        for key, value in changes.items():
            setattr(job, key, value)


def initialize_event_job(event_id: int, progress) -> str:
    event = db.session.get(Event, event_id)
    if not event:
        raise ValueError("Koers niet gevonden.")
    count = initialize_event_from_pcs(event, client=interactive_pcs_client(), progress=progress)
    return f"{count} etappes geladen uit PCS."


def sync_startlist_job(event_id: int, progress) -> str:
    event = db.session.get(Event, event_id)
    if not event:
        raise ValueError("Koers niet gevonden.")
    summary = sync_startlist(
        event,
        client=interactive_pcs_client(),
        progress=progress,
    )
    message = (
        f"Startlijst gesynchroniseerd: {summary.seen_count} renners gezien, "
        f"{len(summary.new_riders)} nieuw, {len(summary.restored_riders)} teruggezet, "
        f"{len(summary.frozen_riders)} bevroren, {len(summary.priced_riders)} geprijsd."
    )
    return message


def enrich_profiles_job(event_id: int, progress) -> str:
    event = db.session.get(Event, event_id)
    if not event:
        raise ValueError("Koers niet gevonden.")
    summary = enrich_missing_profiles(
        event,
        client=interactive_pcs_client(),
        progress=progress,
    )
    message = (
        f"{summary.rider_details_loaded} profielen en "
        f"{summary.team_details_loaded} ploegafbeeldingen bijgewerkt. "
        f"{summary.remaining_riders} profielen resterend."
    )
    if summary.rate_limited:
        message += " PCS gaf een rate-limit; probeer later opnieuw."
    return message


def _wants_json() -> bool:
    return (
        request.headers.get("X-Requested-With") == "fetch"
        or request.accept_mimetypes["application/json"] > request.accept_mimetypes["text/html"]
    )


def interactive_pcs_client() -> PcsClient:
    return PcsClient(timeout=15, request_delay_seconds=2.0, max_retries=2, backoff_seconds=20)


def _direct_pcs_imports_enabled() -> bool:
    configured = current_app.config.get("PCS_DIRECT_IMPORTS_ENABLED")
    if configured is not None:
        return bool(configured)
    return db.engine.dialect.name == "sqlite"


def _direct_pcs_blocked_response(event: Event, stage: Stage | None = None):
    if _direct_pcs_imports_enabled():
        return None
    message = (
        "Directe PCS-imports zijn op deze omgeving uitgeschakeld. "
        "Laad de gegevens lokaal en upload daarna de lokale database via het adminoverzicht."
    )
    if _wants_json():
        return jsonify({"ok": False, "message": message}), 403
    flash(message, "warning")
    if stage:
        return redirect(url_for("events.stage", event_id=event.id, stage_id=stage.id))
    return redirect(url_for("admin.event_detail", event_id=event.id))
