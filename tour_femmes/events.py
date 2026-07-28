from __future__ import annotations

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from tour_femmes import db
from tour_femmes.models import Event, EventEntry, EventRider, Stage, StageLineup, TeamSelection, utcnow
from tour_femmes.scoring import (
    CLASSIFICATION_LABELS,
    DAILY_CLASSIFICATION_POINTS,
    DAILY_LEADER_TEAMMATE_POINTS,
    FINAL_CLASSIFICATION_POINTS,
    FINAL_WINNER_TEAMMATE_POINTS,
    STAGE_WINNER_TEAMMATE_POINTS,
    scoring_rules,
)
from tour_femmes.services.game import (
    build_leaderboard,
    build_rider_stage_history,
    build_stage_leaderboard,
    can_edit_team,
    get_or_create_entry,
    get_team_selection,
    lineup_status,
    save_stage_lineup,
    save_team_selection,
    validate_team_selection,
)
events_bp = Blueprint("events", __name__)


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
                            "total_price": validation.total_price,
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
                        "total_price": validation.total_price,
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
    team_filters = [teams_by_name[name] for name in sorted(teams_by_name, key=str.lower)]
    prices = [link.price for link in event_riders if link.price is not None]
    speciality_filters = [
        {"key": "onedayraces", "label": "Eendagskoersen", "stat_label": "Onedayraces"},
        {"key": "gc", "label": "Klassement", "stat_label": "GC"},
        {"key": "tt", "label": "Tijdrit", "stat_label": "TT"},
        {"key": "sprint", "label": "Sprint", "stat_label": "Sprint"},
        {"key": "climber", "label": "Klimmen", "stat_label": "Climber"},
        {"key": "hills", "label": "Heuvels", "stat_label": "Hills"},
    ]
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
    )


@events_bp.route("/events/<int:event_id>/stages/<int:stage_id>", methods=["GET", "POST"])
@login_required
def stage(event_id: int, stage_id: int):
    event = Event.query.get_or_404(event_id)
    stage_obj = Stage.query.filter_by(id=stage_id, event_id=event.id).first_or_404()
    selection = get_team_selection(current_user, event)
    entry = EventEntry.query.filter_by(user_id=current_user.id, event_id=event.id, status="active").first()

    if not entry:
        flash("Schrijf je eerst in voor de koers voordat je een etappeselectie maakt.", "warning")
        return redirect(url_for("events.team", event_id=event.id))
    if not selection or len(selection.riders) != event.team_size:
        flash("Maak eerst je teamselectie compleet voordat je een etappeselectie maakt.", "warning")
        return redirect(url_for("events.team", event_id=event.id))

    locked = stage_obj.is_locked()
    if request.method == "POST":
        wants_json = _wants_json()
        if locked:
            message = "Deze etappeselectie is gesloten omdat de etappe is gestart."
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
    captain_id = lineup.captain_event_rider_id if lineup else None
    user_result = next((score for score in stage_obj.user_scores if score.user_id == current_user.id), None)
    team_riders = [link.event_rider for link in selection.riders]
    rider_history = build_rider_stage_history(event, stage_obj, team_riders)
    show_results = stage_obj.has_ranked_result()

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
        user_result=user_result,
        rider_history=rider_history,
    )


@events_bp.route("/events/<int:event_id>/leaderboard")
@login_required
def leaderboard(event_id: int):
    event = Event.query.get_or_404(event_id)
    selected_stage = None
    selected_stage_number = request.args.get("stage", type=int)
    if selected_stage_number is not None:
        selected_stage = next(
            (stage for stage in event.stages if stage.number == selected_stage_number),
            None,
        )
        if selected_stage is None:
            abort(404)

    rows = build_leaderboard(event) if selected_stage is None else []
    stage_rows = build_stage_leaderboard(event, selected_stage) if selected_stage else []
    return render_template(
        "events/leaderboard.html",
        event=event,
        rows=rows,
        selected_stage=selected_stage,
        stage_rows=stage_rows,
        lineups_visible=selected_stage.is_locked() if selected_stage else False,
    )


@events_bp.route("/events/<int:event_id>/scoring")
@login_required
def scoring(event_id: int):
    event = Event.query.get_or_404(event_id)
    return render_template(
        "events/scoring.html",
        event=event,
        scoring_rules=scoring_rules(),
        classification_labels=CLASSIFICATION_LABELS,
        daily_classification_points=DAILY_CLASSIFICATION_POINTS,
        daily_teammate_points=DAILY_LEADER_TEAMMATE_POINTS,
        final_classification_points=FINAL_CLASSIFICATION_POINTS,
        final_teammate_points=FINAL_WINNER_TEAMMATE_POINTS,
        stage_winner_teammate_points=STAGE_WINNER_TEAMMATE_POINTS,
    )


def _selection_finished(event: Event, selection: TeamSelection | None) -> bool:
    return bool(selection and len(selection.riders) == event.team_size and selection.total_price <= event.budget)


def _wants_json() -> bool:
    return (
        request.headers.get("X-Requested-With") == "fetch"
        or request.accept_mimetypes["application/json"] > request.accept_mimetypes["text/html"]
    )
