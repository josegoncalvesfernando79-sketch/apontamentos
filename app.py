from flask import Flask, redirect, url_for

from models.db import init_db, seed_data
from routes.auth_routes import auth_bp
from routes.main_routes import main_bp
from services.backup_service import schedule_backup


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "sigef-secret-key-local"
    app.config["DATABASE"] = "sigef.db"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    init_db(app.config["DATABASE"])
    seed_data(app.config["DATABASE"])

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    schedule_backup(app.config["DATABASE"])

    @app.route("/")
    def index():
        return redirect(url_for("main.dashboard"))

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="127.0.0.1", port=5000, debug=False)
