"""
AI_Mail_App — Flask Application Factory
Phase 1: Skeleton only. Auth and routes added in Phase 2+.
"""
from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "change-this-before-production"

    # Register blueprints here as we build each phase
    # from app.routes.auth import auth_bp
    # app.register_blueprint(auth_bp)

    @app.route("/")
    def index():
        return "<h1>AI Mail App — Phase 1 Running ✅</h1><p>Setup complete. Proceed to Phase 2.</p>"

    return app
