from __future__ import annotations

import secrets

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from tour_femmes import db
from tour_femmes.models import (
    Event,
    EventEntry,
    EventRider,
    Stage,
    StageLineup,
    Subleague,
    SubleagueMember,
    TeamSelection,
    utcnow,
)
from tour_femmes.scoring import (
    CLASSIFICATION_LABELS,
    DAILY_CLASSIFICATION_POINTS,
    DAILY_LEADER_TEAMMATE_POINTS,
    FINAL_CLASSIFICATION_POINTS,
    FINAL_WINNER_TEAMMATE_POINTS,
    STAGE_WINNER_TEAMMATE_POINTS,
    points_table_for_event,
    points_table_for_stage,
    scoring_rules,
)
from tour_femmes.services.game import (
    build_final_classification_leaderboard,
    build_leaderboard,
    build_official_stage_scores,
    build_rider_stage_history,
    build_stage_leaderboard,
    build_team_selection_overview,
    can_edit_team,
    event_selection_progress,
    final_classification_stage,
    get_or_create_entry,
    get_team_selection,
    lineup_status,
    save_stage_lineup,
    save_team_selection,
    unavailable_rider_statuses,
    validate_team_selection,
)
events_bp = Blueprint("events", __name__)
SUBLEAGUE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
RIDER_SPECIALITY_FILTERS = [
    {"key": "onedayraces", "label": "Eendagskoersen", "stat_label": "Onedayraces"},
    {"key": "gc", "label": "Klassement", "stat_label": "GC"},
    {"key": "tt", "label": "Tijdrit", "stat_label": "TT"},
    {"key": "sprint", "label": "Sprint", "stat_label": "Sprint"},
    {"key": "climber", "label": "Klimmen", "stat_label": "Climber"},
    {"key": "hills", "label": "Heuvels", "stat_label": "Hills"},
]


@events_bp.app_context_processor
def inject_event_navigation_helpers():
    return {"event_selection_progress": event_selection_progress}


@events_bp.route("/events")
@login_required
def overview():
    now = utcnow()
    events = Event.query.filter_by(status="active").order_by(Event.created_at.desc()).all()
    entries = {
        entry.event_id: entry
        for entry in EventEntry.query.filter_by(user_id=current_user.id, status="active").all()
    }
    selections = {
        selection.event_id: selection
        for selection in TeamSelection.query.filter_by(user_id=current_user.id).all()
    }
    cards = []
    for event in events:
        next_stage = event.next_stage(now)
        cards.append(
            {
                "event": event,
                "entry": entries.get(event.id),
                "selection": selections.get(event.id),
                "selection_finished": _selection_finished(event, selections.get(event.id)),
                "join_open": can_edit_team(event, now),
                "next_stage": next_stage,
                "next_lineup_status": lineup_status(current_user, next_stage) if next_stage else "Klaar",
            }
        )
    return render_template("events/overview.html", cards=cards, now=now)


@events_bp.route("/events/<int:event_id>")
@login_required
def event_home(event_id: int):
    event = Event.query.get_or_404(event_id)
    if can_edit_team(event):
        return redirect(url_for("events.team", event_id=event.id))
    next_stage = event.next_stage()
    if next_stage:
        return redirect(url_for("events.stage", event_id=event.id, stage_id=next_stage.id))
    return redirect(url_for("events.leaderboard", event_id=event.id))


@events_bp.route("/events/<int:event_id>/join", methods=["POST"])
@login_required
def join(event_id: int):
    event = Event.query.get_or_404(event_id)
    if not can_edit_team(event):
        flash("De inschrijving is gesloten omdat de teamselectiedeadline is verstreken.", "warning")
        return redirect(url_for("events.overview"))
    get_or_create_entry(current_user, event)
    db.session.commit()
    flash("Je doet mee aan deze koers.", "success")
    return redirect(url_for("events.team", event_id=event.id))


@events_bp.route("/events/<int:event_id>/team", methods=["GET", "POST"])
@login_required
def team(event_id: int):
    event = Event.query.get_or_404(event_id)
    selection = get_team_selection(current_user, event)
    editable = can_edit_team(event)

    if request.method == "POST":
        wants_json = _wants_json()
        if not editable:
            message = "De teamselectie is gesloten omdat de koers is gestart."
            if wants_json:
                return jsonify({"ok": False, "message": message}), 423
            flash(message, "danger")
            return redirect(url_for("events.team", event_id=event.id))

        validation = validate_team_selection(event, request.form.getlist("riders"), require_exact=not wants_json)
        if not validation.ok:
            if wants_json:
                return (
                    jsonify(
                        {
                            "ok": False,
                            "message": validation.message,
                            "count": len(validation.selected_riders),
                            "total_price": float(validation.total_price),
                            "complete": False,
                        }
                    ),
                    400,
                )
            flash(validation.message, "danger")
        else:
            save_team_selection(current_user, event, validation.selected_riders, validation.total_price)
            db.session.commit()
            if wants_json:
                return jsonify(
                    {
                        "ok": True,
                        "message": validation.message,
                        "count": len(validation.selected_riders),
                        "total_price": float(validation.total_price),
                        "complete": len(validation.selected_riders) == event.team_size,
                    }
                )
            flash(validation.message, "success")
            return redirect(url_for("events.event_home", event_id=event.id))

    event_riders = (
        EventRider.query.filter_by(event_id=event.id, active=True, frozen=False)
        .filter(EventRider.price.isnot(None))
        .join(EventRider.rider)
        .order_by(EventRider.price.desc(), EventRider.id)
        .all()
    )
    teams_by_name = {link.team.name: link.team for link in event_riders if link.team}
    team_price_totals = {
        name: sum(link.price for link in event_riders if link.team and link.team.name == name)
        for name in teams_by_name
    }
    team_filters = [
        teams_by_name[name]
        for name in sorted(teams_by_name, key=lambda name: (-team_price_totals[name], name.lower()))
    ]
    prices = [link.price for link in event_riders if link.price is not None]
    speciality_filters = RIDER_SPECIALITY_FILTERS
    selected_ids = selection.rider_ids() if selection else set()
    selected_total = selection.total_price if selection else 0
    remaining_budget = event.budget - selected_total
    completion_percent = round((len(selected_ids) / event.team_size) * 100) if event.team_size else 0
    budget_percent = round((selected_total / event.budget) * 100) if event.budget else 0
    team_status = {
        "selected_count": len(selected_ids),
        "selected_total": selected_total,
        "remaining_riders": max(event.team_size - len(selected_ids), 0),
        "remaining_budget": remaining_budget,
        "completion_percent": min(completion_percent, 100),
        "budget_percent": max(min(budget_percent, 100), 0),
        "complete": len(selected_ids) == event.team_size and selected_total <= event.budget,
        "over_budget": selected_total > event.budget,
    }
    stage_participation: dict[int, list[Stage]] = {}
    selected_stage_counts: dict[int, int] = {}
    rider_genders: dict[int, list[str]] = {}
    event_genders: set[str] = set()
    if event.is_custom:
        for stage_obj in event.stages:
            selected_stage_counts[stage_obj.id] = 0
            stage_gender = stage_obj.participant_gender
            if stage_gender:
                event_genders.add(stage_gender)
            for stage_rider in stage_obj.rider_links:
                stage_participation.setdefault(stage_rider.event_rider_id, []).append(stage_obj)
                if stage_gender:
                    genders = rider_genders.setdefault(stage_rider.event_rider_id, [])
                    if stage_gender not in genders:
                        genders.append(stage_gender)
                if stage_rider.event_rider_id in selected_ids:
                    selected_stage_counts[stage_obj.id] += 1
    show_gender_filter = {"men", "women"}.issubset(event_genders)
    race_filter_groups: list[dict] = []
    if event.is_custom:
        if show_gender_filter:
            for gender, label, all_label in (
                ("women", "Vrouwen", "Alle vrouwen"),
                ("men", "Mannen", "Alle mannen"),
            ):
                stages = [stage_obj for stage_obj in event.stages if stage_obj.participant_gender == gender]
                if stages:
                    race_filter_groups.append(
                        {"label": label, "gender": gender, "all_label": all_label, "stages": stages}
                    )
            other_stages = [stage_obj for stage_obj in event.stages if not stage_obj.participant_gender]
            if other_stages:
                race_filter_groups.append(
                    {"label": "Overige onderdelen", "gender": "", "all_label": "", "stages": other_stages}
                )
        else:
            race_filter_groups.append(
                {"label": "Onderdelen", "gender": "", "all_label": "", "stages": event.stages}
            )
    return render_template(
        "events/team.html",
        event=event,
        event_riders=event_riders,
        selected_ids=selected_ids,
        selection=selection,
        editable=editable,
        team_status=team_status,
        team_filters=team_filters,
        speciality_filters=speciality_filters,
        price_min=min(prices, default=0),
        price_max=max(prices, default=0),
        stage_participation=stage_participation,
        selected_stage_counts=selected_stage_counts,
        rider_genders=rider_genders,
        show_gender_filter=show_gender_filter,
        race_filter_groups=race_filter_groups,
    )


@events_bp.route("/events/<int:event_id>/stages/<int:stage_id>", methods=["GET", "POST"])
@login_required
def stage(event_id: int, stage_id: int):
    event = Event.query.get_or_404(event_id)
    stage_obj = Stage.query.filter_by(id=stage_id, event_id=event.id).first_or_404()
    selection = get_team_selection(current_user, event)
    entry = EventEntry.query.filter_by(user_id=current_user.id, event_id=event.id, status="active").first()

    if not entry:
        selection_label = "opstelling" if event.is_custom else "etappeselectie"
        flash(f"Schrijf je eerst in voor de koers voordat je een {selection_label} maakt.", "warning")
        return redirect(url_for("events.team", event_id=event.id))
    if not selection or len(selection.riders) != event.team_size:
        selection_label = "opstelling" if event.is_custom else "etappeselectie"
        flash(f"Maak eerst je teamselectie compleet voordat je een {selection_label} maakt.", "warning")
        return redirect(url_for("events.team", event_id=event.id))

    locked = stage_obj.is_locked()
    if request.method == "POST":
        wants_json = _wants_json()
        if locked:
            message = (
                "Deze opstelling is gesloten omdat het onderdeel is gestart."
                if event.is_custom
                else "Deze etappeselectie is gesloten omdat de etappe is gestart."
            )
            if wants_json:
                return jsonify({"ok": False, "message": message}), 423
            flash(message, "danger")
            return redirect(url_for("events.stage", event_id=event.id, stage_id=stage_obj.id))
        captain_raw = request.form.get("captain")
        captain_id = int(captain_raw) if captain_raw and captain_raw.isdigit() else 0
        rider_ids = request.form.getlist("riders")
        ok, message = save_stage_lineup(
            current_user,
            stage_obj,
            rider_ids,
            captain_id,
            require_exact=not wants_json,
        )
        if wants_json:
            count = len({rider_id for rider_id in rider_ids})
            status_code = 200 if ok else 400
            if ok:
                db.session.commit()
            return (
                jsonify(
                    {
                        "ok": ok,
                        "message": message,
                        "count": count,
                        "complete": ok and count == event.lineup_size,
                    }
                ),
                status_code,
            )
        flash(message, "success" if ok else "danger")
        if ok:
            db.session.commit()
            return redirect(url_for("events.stage", event_id=event.id, stage_id=stage_obj.id))

    lineup = StageLineup.query.filter_by(user_id=current_user.id, stage_id=stage_obj.id).first()
    selected_ids = lineup.rider_ids() if lineup else set()
    unavailable_statuses = unavailable_rider_statuses(stage_obj)
    if not locked:
        selected_ids -= set(unavailable_statuses)
    captain_id = lineup.captain_event_rider_id if lineup else None
    if captain_id not in selected_ids:
        captain_id = next(iter(selected_ids), None)
    user_result = next((score for score in stage_obj.user_scores if score.user_id == current_user.id), None)
    team_riders = [link.event_rider for link in selection.riders]
    team_rider_ids = {event_rider.id for event_rider in team_riders}
    rider_history = build_rider_stage_history(event, stage_obj, team_riders)
    stage_participation: dict[int, list[Stage]] = {}
    if event.is_custom:
        for event_stage in event.stages:
            for stage_rider in event_stage.rider_links:
                stage_participation.setdefault(stage_rider.event_rider_id, []).append(event_stage)
    show_results = stage_obj.has_ranked_result()
    stage_results = sorted(
        stage_obj.results,
        key=lambda result: (
            result.rank is None,
            result.rank if result.rank is not None else 0,
            result.event_rider.rider.name.casefold(),
        ),
    )
    stage_results_by_rider_id = {
        result.event_rider_id: result for result in stage_results
    }
    official_rider_scores = (
        build_official_stage_scores(stage_obj, include_final_classification=False)
        if show_results
        else {}
    )
    personal_final_rider_scores = tuple(sorted(
        (
            rider_score
            for rider_score in user_result.rider_scores
            if rider_score.final_classification_points or rider_score.final_teammate_points
        ),
        key=lambda rider_score: -(
            rider_score.final_classification_points + rider_score.final_teammate_points
        ),
    )) if user_result else ()
    personal_stage_rider_scores = tuple(sorted(
        (
            rider_score
            for rider_score in user_result.rider_scores
            if rider_score.event_rider_id in selected_ids
        ),
        key=lambda rider_score: -(
            rider_score.total_points
            - rider_score.final_classification_points
            - rider_score.final_teammate_points
        ),
    )) if user_result else ()
    personal_final_score = sum(
        rider_score.final_classification_points + rider_score.final_teammate_points
        for rider_score in personal_final_rider_scores
    )
    personal_stage_score = (
        user_result.score - personal_final_score
        if user_result
        else 0
    )

    return render_template(
        "events/stage.html",
        event=event,
        stage=stage_obj,
        team_riders=team_riders,
        selected_ids=selected_ids,
        captain_id=captain_id,
        locked=locked,
        lineup=lineup,
        show_results=show_results,
        stage_results=stage_results,
        stage_results_by_rider_id=stage_results_by_rider_id,
        team_rider_ids=team_rider_ids,
        official_rider_scores=official_rider_scores,
        user_result=user_result,
        personal_stage_rider_scores=personal_stage_rider_scores,
        personal_stage_score=personal_stage_score,
        personal_final_score=personal_final_score,
        personal_final_rider_scores=personal_final_rider_scores,
        rider_history=rider_history,
        stage_participation=stage_participation,
        unavailable_statuses=unavailable_statuses,
        speciality_filters=RIDER_SPECIALITY_FILTERS,
    )


@events_bp.route("/events/<int:event_id>/leaderboard")
@login_required
def leaderboard(event_id: int):
    event = Event.query.get_or_404(event_id)
    joined_subleagues = (
        Subleague.query.join(SubleagueMember)
        .filter(
            Subleague.event_id == event.id,
            SubleagueMember.user_id == current_user.id,
        )
        .order_by(func.lower(Subleague.name))
        .all()
    )
    selected_subleague = None
    selected_subleague_id = request.args.get("league", type=int)
    if selected_subleague_id is not None:
        selected_subleague = next(
            (league for league in joined_subleagues if league.id == selected_subleague_id),
            None,
        )
        if selected_subleague is None:
            abort(404)

    selected_stage = None
    selected_stage_value = request.args.get("stage", "")
    selected_final = selected_stage_value == "final"
    selected_stage_number = request.args.get("stage", type=int) if not selected_final else None
    if selected_stage_number is not None:
        selected_stage = next(
            (stage for stage in event.stages if stage.number == selected_stage_number),
            None,
        )
        if selected_stage is None:
            abort(404)

    member_ids = selected_subleague.member_ids() if selected_subleague else None
    final_stage = final_classification_stage(event)
    if selected_final and final_stage is None:
        abort(404)
    rows = (
        build_leaderboard(event, member_ids)
        if selected_stage is None and not selected_final
        else []
    )
    if selected_final:
        stage_rows = build_final_classification_leaderboard(event, member_ids)
    elif selected_stage:
        stage_rows = build_stage_leaderboard(event, selected_stage, member_ids)
    else:
        stage_rows = []
    return render_template(
        "events/leaderboard.html",
        event=event,
        rows=rows,
        joined_subleagues=joined_subleagues,
        selected_subleague=selected_subleague,
        selected_stage=selected_stage,
        selected_final=selected_final,
        final_stage=final_stage,
        stage_rows=stage_rows,
        lineups_visible=True if selected_final else selected_stage.is_locked() if selected_stage else False,
    )


@events_bp.route("/events/<int:event_id>/teams")
@login_required
def teams(event_id: int):
    event = Event.query.get_or_404(event_id)
    if not event.has_started():
        flash("Teams zijn zichtbaar zodra de deadline voor teamselectie voorbij is.", "info")
        return redirect(url_for("events.event_home", event_id=event.id))
    return render_template(
        "events/teams.html",
        event=event,
        overview=build_team_selection_overview(event),
    )


@events_bp.route("/events/<int:event_id>/subleagues")
@login_required
def subleagues(event_id: int):
    event = Event.query.get_or_404(event_id)
    entry = EventEntry.query.filter_by(
        user_id=current_user.id,
        event_id=event.id,
        status="active",
    ).first()
    joined_subleagues = (
        Subleague.query.join(SubleagueMember)
        .filter(
            Subleague.event_id == event.id,
            SubleagueMember.user_id == current_user.id,
        )
        .order_by(func.lower(Subleague.name))
        .all()
    )
    return render_template(
        "events/subleagues.html",
        event=event,
        entry=entry,
        join_open=can_edit_team(event),
        joined_subleagues=joined_subleagues,
    )


@events_bp.route("/events/<int:event_id>/subleagues/create", methods=["POST"])
@login_required
def create_subleague(event_id: int):
    event = Event.query.get_or_404(event_id)
    if not _is_event_participant(event):
        flash("Schrijf je eerst in voor deze koers.", "warning")
        return redirect(url_for("events.subleagues", event_id=event.id))

    name = " ".join(request.form.get("name", "").split())
    if len(name) < 2 or len(name) > 80:
        flash("Een subcompetitienaam moet tussen 2 en 80 tekens lang zijn.", "danger")
        return redirect(url_for("events.subleagues", event_id=event.id))
    existing = Subleague.query.filter(
        Subleague.event_id == event.id,
        func.lower(Subleague.name) == name.lower(),
    ).first()
    if existing:
        flash("Binnen deze koers bestaat al een subcompetitie met die naam.", "danger")
        return redirect(url_for("events.subleagues", event_id=event.id))

    subleague = Subleague(
        event=event,
        owner=current_user,
        name=name,
        join_code=_generate_subleague_code(),
    )
    subleague.memberships.append(SubleagueMember(user=current_user))
    db.session.add(subleague)
    db.session.commit()
    flash(f"Subcompetitie {name} is aangemaakt.", "success")
    return redirect(url_for("events.subleagues", event_id=event.id))


@events_bp.route("/events/<int:event_id>/subleagues/join", methods=["POST"])
@login_required
def join_subleague(event_id: int):
    event = Event.query.get_or_404(event_id)
    if not _is_event_participant(event):
        flash("Schrijf je eerst in voor deze koers.", "warning")
        return redirect(url_for("events.subleagues", event_id=event.id))

    join_code = _normalize_subleague_code(request.form.get("join_code", ""))
    subleague = Subleague.query.filter_by(
        event_id=event.id,
        join_code=join_code,
    ).first()
    if not subleague:
        flash("Deze deelnamecode is niet geldig voor deze koers.", "danger")
        return redirect(url_for("events.subleagues", event_id=event.id))
    membership = SubleagueMember.query.filter_by(
        subleague_id=subleague.id,
        user_id=current_user.id,
    ).first()
    if membership:
        flash(f"Je neemt al deel aan {subleague.name}.", "info")
        return redirect(url_for("events.subleagues", event_id=event.id))

    db.session.add(SubleagueMember(subleague=subleague, user=current_user))
    db.session.commit()
    flash(f"Je bent toegevoegd aan {subleague.name}.", "success")
    return redirect(url_for("events.subleagues", event_id=event.id))


@events_bp.route(
    "/events/<int:event_id>/subleagues/<int:subleague_id>/leave",
    methods=["POST"],
)
@login_required
def leave_subleague(event_id: int, subleague_id: int):
    event = Event.query.get_or_404(event_id)
    subleague = Subleague.query.filter_by(id=subleague_id, event_id=event.id).first_or_404()
    if subleague.owner_id == current_user.id:
        flash("Als beheerder kun je deze subcompetitie verwijderen, maar niet verlaten.", "warning")
        return redirect(url_for("events.subleagues", event_id=event.id))
    membership = SubleagueMember.query.filter_by(
        subleague_id=subleague.id,
        user_id=current_user.id,
    ).first_or_404()
    db.session.delete(membership)
    db.session.commit()
    flash(f"Je hebt {subleague.name} verlaten.", "success")
    return redirect(url_for("events.subleagues", event_id=event.id))


@events_bp.route(
    "/events/<int:event_id>/subleagues/<int:subleague_id>/delete",
    methods=["POST"],
)
@login_required
def delete_subleague(event_id: int, subleague_id: int):
    event = Event.query.get_or_404(event_id)
    subleague = Subleague.query.filter_by(id=subleague_id, event_id=event.id).first_or_404()
    if subleague.owner_id != current_user.id:
        abort(403)
    if request.form.get("confirm_name", "").strip() != subleague.name:
        flash("Typ de naam van de subcompetitie exact over om deze te verwijderen.", "danger")
        return redirect(url_for("events.subleagues", event_id=event.id))

    name = subleague.name
    db.session.delete(subleague)
    db.session.commit()
    flash(f"Subcompetitie {name} is verwijderd.", "success")
    return redirect(url_for("events.subleagues", event_id=event.id))


@events_bp.route("/events/<int:event_id>/scoring")
@login_required
def scoring(event_id: int):
    event = Event.query.get_or_404(event_id)
    scoring_groups_by_table: dict[tuple[tuple[int, int], ...], dict[str, object]] = {}
    for stage in event.stages:
        points_by_rank = points_table_for_stage(stage)
        key = tuple(sorted(points_by_rank.items()))
        group = scoring_groups_by_table.setdefault(
            key,
            {
                "rules": scoring_rules(points_by_rank),
                "stages": [],
            },
        )
        group["stages"].append(stage)
    scoring_groups = list(scoring_groups_by_table.values())
    if not scoring_groups:
        event_points = points_table_for_event(event)
        scoring_groups.append({"rules": scoring_rules(event_points), "stages": []})
    return render_template(
        "events/scoring.html",
        event=event,
        scoring_groups=scoring_groups,
        classification_labels=CLASSIFICATION_LABELS,
        daily_classification_points=DAILY_CLASSIFICATION_POINTS,
        daily_teammate_points=DAILY_LEADER_TEAMMATE_POINTS,
        final_classification_points=FINAL_CLASSIFICATION_POINTS,
        final_teammate_points=FINAL_WINNER_TEAMMATE_POINTS,
        stage_winner_teammate_points=STAGE_WINNER_TEAMMATE_POINTS,
    )


def _selection_finished(event: Event, selection: TeamSelection | None) -> bool:
    return bool(selection and len(selection.riders) == event.team_size and selection.total_price <= event.budget)


def _is_event_participant(event: Event) -> bool:
    return bool(
        EventEntry.query.filter_by(
            user_id=current_user.id,
            event_id=event.id,
            status="active",
        ).first()
    )


def _generate_subleague_code() -> str:
    while True:
        code = "".join(secrets.choice(SUBLEAGUE_CODE_ALPHABET) for _ in range(8))
        if not Subleague.query.filter_by(join_code=code).first():
            return code


def _normalize_subleague_code(value: str) -> str:
    return "".join(character for character in value.upper() if character.isalnum())


def _wants_json() -> bool:
    return (
        request.headers.get("X-Requested-With") == "fetch"
        or request.accept_mimetypes["application/json"] > request.accept_mimetypes["text/html"]
    )
