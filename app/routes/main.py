"""
app/routes/main.py
Main routes — inbox placeholder (Phase 3 will build the real inbox).
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@main_bp.route("/inbox")
@login_required
def inbox():
    return render_template("inbox.html", user=current_user)
