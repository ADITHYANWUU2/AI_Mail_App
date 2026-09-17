"""
AI_Mail_App — Flask Application Factory  (Phase 3)
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from flask_login import LoginManager
from database import init_db
from app.models.user import User


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "ai-mail-secret-2024-change-in-prod"

    upload_folder = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max

    with app.app_context():
        init_db()

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view              = "auth.login"
    login_manager.login_message           = "🔒 Please log in to access your inbox."
    login_manager.login_message_category  = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))

    # ── Blueprints ───────────────────────────────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.mail import mail_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(mail_bp)

    # ── Error Handlers ────────────────────────────────────────────────────────
    from flask import render_template

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("500.html"), 500

    return app
