
from flask import Blueprint, jsonify, current_app
from sqlalchemy import text

from ..extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.get("")
def api_root():
    return jsonify({
        "success": True,
        "message": "Bienvenue sur l'API BiblioTech.",
        "status": "running"
    }), 200


@health_bp.get("/health")
def health_check():
    return jsonify({
        "success": True,
        "message": "BiblioTech API is running.",
        "status": "healthy"
    }), 200


@health_bp.get("/health/database")
def database_health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({
            "success": True,
            "database": "connected"
        }), 200

    except Exception:
        current_app.logger.exception(
            "ERREUR DE CONNEXION A LA BASE DE DONNEES"
        )
        db.session.rollback()

        return jsonify({
            "success": False,
            "database": "unavailable",
            "message": "Connexion à la base de données impossible."
        }), 503
