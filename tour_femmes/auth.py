from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from tour_femmes import db
from tour_femmes.models import Event, EventEntry, User
from tour_femmes.services.deletion import delete_user_account

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


@auth_bp.route("/account")
@login_required
def account():
    return render_template("auth/account.html")


@auth_bp.route("/account/profile", methods=["POST"])
@login_required
def update_profile():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip() or None
    current_password = request.form.get("current_password", "")

    if not check_password_hash(current_user.password_hash, current_password):
        flash("Je huidige wachtwoord klopt niet.", "danger")
        return redirect(url_for("auth.account"))
    if not username:
        flash("Gebruikersnaam is verplicht.", "danger")
        return redirect(url_for("auth.account"))
    if User.query.filter(User.username == username, User.id != current_user.id).first():
        flash("Die gebruikersnaam is al in gebruik.", "danger")
        return redirect(url_for("auth.account"))
    if email and User.query.filter(User.email == email, User.id != current_user.id).first():
        flash("Dat e-mailadres is al geregistreerd.", "danger")
        return redirect(url_for("auth.account"))

    current_user.username = username
    current_user.email = email
    db.session.commit()
    flash("Profiel opgeslagen.", "success")
    return redirect(url_for("auth.account"))


@auth_bp.route("/account/password", methods=["POST"])
@login_required
def update_password():
    current_password = request.form.get("current_password", "")
    password = request.form.get("password", "")
    confirm = request.form.get("confirm", "")

    if not check_password_hash(current_user.password_hash, current_password):
        flash("Je huidige wachtwoord klopt niet.", "danger")
        return redirect(url_for("auth.account"))
    if not password:
        flash("Nieuw wachtwoord is verplicht.", "danger")
        return redirect(url_for("auth.account"))
    if password != confirm:
        flash("Wachtwoorden komen niet overeen.", "danger")
        return redirect(url_for("auth.account"))

    current_user.password_hash = generate_password_hash(password)
    db.session.commit()
    flash("Wachtwoord bijgewerkt.", "success")
    return redirect(url_for("auth.account"))


@auth_bp.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    current_password = request.form.get("current_password", "")
    confirm_username = request.form.get("confirm_username", "").strip()
    username = current_user.username
    user = db.session.get(User, current_user.id)

    if not user or not check_password_hash(user.password_hash, current_password):
        flash("Je huidige wachtwoord klopt niet.", "danger")
        return redirect(url_for("auth.account"))
    if confirm_username != username:
        flash("Typ je gebruikersnaam exact over om je account te verwijderen.", "danger")
        return redirect(url_for("auth.account"))

    logout_user()
    delete_user_account(user)
    db.session.commit()
    flash("Je account is verwijderd.", "success")
    return redirect(url_for("auth.login"))


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
