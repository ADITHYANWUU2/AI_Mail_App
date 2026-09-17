"""
app/routes/auth.py — Register / Login / Logout
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User

auth_bp = Blueprint("auth", __name__)


# ── Register ─────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("mail.inbox"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email",    "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        # ── Validation ────────────────────────────────────────────────────────
        if not all([username, email, password, confirm]):
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if len(username) < 3:
            flash("Username must be at least 3 characters.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        # ── Create user (hashes password internally) ──────────────────────────
        user = User.register(username, email, password)
        if user is None:
            flash("Username or email already taken. Try a different one.", "danger")
            return render_template("register.html")

        login_user(user, remember=True)
        flash(f"🎉 Welcome, {user.username}! Account created successfully.", "success")
        return redirect(url_for("mail.inbox"))

    return render_template("register.html")


# ── Login ─────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("mail.inbox"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        row = User.get_by_username(username)

        # Verify: user exists AND password matches hash
        if row and User.verify_password(row["password_hash"], password):
            user = User(row["id"], row["username"], row["email"])
            login_user(user, remember=True)
            flash(f"👋 Welcome back, {user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("mail.inbox"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


# ── Logout ────────────────────────────────────────────────────────────────────
@auth_bp.route("/logout")
@login_required
def logout():
    name = current_user.username
    logout_user()
    flash(f"👋 Goodbye, {name}! You have been logged out.", "info")
    return redirect(url_for("auth.login"))
