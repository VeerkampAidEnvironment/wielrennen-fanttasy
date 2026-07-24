from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from tour_femmes import db
from tour_femmes.models import Event, EventEntry, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(default_after_login_url(current_user))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(default_after_login_url(current_user))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Ongeldige gebruikersnaam of ongeldig wachtwoord.", "danger")
            return render_template("auth/login.html", username=username)

        login_user(user)
        next_url = request.args.get("next")
        return redirect(next_url or default_after_login_url(user))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(default_after_login_url(current_user))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip() or None
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or not password:
            flash("Gebruikersnaam en wachtwoord zijn verplicht.", "danger")
            return render_template("auth/register.html", username=username, email=email)
        if password != confirm:
            flash("Wachtwoorden komen niet overeen.", "danger")
            return render_template("auth/register.html", username=username, email=email)
        if User.query.filter_by(username=username).first():
            flash("Die gebruikersnaam is al in gebruik.", "danger")
            return render_template("auth/register.html", username=username, email=email)
        if email and User.query.filter_by(email=email).first():
            flash("Dat e-mailadres is al geregistreerd.", "danger")
            return render_template("auth/register.html", username=username, email=email)

        user = User(username=username, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Welkom. Je account is klaar.", "success")
        return redirect(default_after_login_url(user))

    return render_template("auth/register.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Je bent uitgelogd.", "info")
    return redirect(url_for("auth.login"))


def default_after_login_url(user: User) -> str:
    active_events = Event.query.filter_by(status="active").order_by(Event.created_at.desc()).all()
    if len(active_events) == 1:
        event = active_events[0]
        entry = EventEntry.query.filter_by(user_id=user.id, event_id=event.id, status="active").first()
        if entry:
            return url_for("events.event_home", event_id=event.id)
    return url_for("events.overview")
