from flask import Blueprint, jsonify
from sqlalchemy import text
from app.extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    return jsonify({
        "success": True,
        "message": "BiblioTech API is running.",
        "status": "healthy",
    }), 200


@health_bp.get("/health/database")
def database_health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"success": True, "database": "connected"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({
            "success": False,
            "database": "unavailable",
            "message": "Connexion à la base de données impossible.",
        }), 503
