import os
from flask import Flask, jsonify
from flask_cors import CORS

from app.config import Config
from app.extensions import bcrypt, db, jwt, migrate
from app.routes import register_routes


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    CORS(app, resources={r"/api/*": {"origins": [frontend_url]}})

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)

    # Import models so Flask-Migrate can detect them.
    from app import models  # noqa: F401

    register_routes(app)

    @app.get("/")
    def index():
        return jsonify({
            "success": True,
            "message": "Bienvenue sur l'API BiblioTech.",
            "status": "running",
        }), 200

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"success": False, "message": "Route introuvable."}), 404

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        return jsonify({"success": False, "message": "Erreur interne du serveur."}), 500

    return app
