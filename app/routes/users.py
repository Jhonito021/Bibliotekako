from flask import Blueprint, jsonify, request
from sqlalchemy import select
from app.extensions import db
from app.models import User
from app.utils.security import roles_required

users_bp = Blueprint("users", __name__)


@users_bp.get("")
@roles_required("admin")
def list_users():
    users = db.session.scalars(select(User).order_by(User.id.desc())).all()
    return jsonify({"success": True, "count": len(users), "users": [u.to_dict() for u in users]}), 200


@users_bp.patch("/<int:user_id>/status")
@roles_required("admin")
def update_user_status(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "message": "Utilisateur introuvable."}), 404

    data = request.get_json(silent=True) or {}
    if not isinstance(data.get("is_active"), bool):
        return jsonify({"success": False, "message": "Le champ is_active doit être un booléen."}), 400

    user.is_active = data["is_active"]
    db.session.commit()
    return jsonify({"success": True, "user": user.to_dict()}), 200


@users_bp.patch("/<int:user_id>/role")
@roles_required("admin")
def update_user_role(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "message": "Utilisateur introuvable."}), 404

    data = request.get_json(silent=True) or {}
    role = data.get("role")
    if role not in {"admin", "librarian", "reader"}:
        return jsonify({
            "success": False,
            "message": "Rôle invalide. Valeurs autorisées : admin, librarian, reader.",
        }), 400

    user.role = role
    db.session.commit()
    return jsonify({"success": True, "user": user.to_dict()}), 200
