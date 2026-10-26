from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from sqlalchemy import select
from backend.app.extensions import bcrypt, db
from backend.app.models import User

auth_bp = Blueprint("auth", __name__)
VALID_ROLES = {"admin", "librarian", "reader"}


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    full_name = str(data.get("full_name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not full_name or not email or not isinstance(password, str) or len(password) < 8:
        return jsonify({
            "success": False,
            "message": "full_name, email et mot de passe (8 caractères minimum) sont requis.",
        }), 400

    if db.session.scalar(select(User).where(User.email == email)):
        return jsonify({"success": False, "message": "Cette adresse e-mail est déjà utilisée."}), 409

    user = User(
        full_name=full_name,
        email=email,
        password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
        role="reader",
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"success": True, "message": "Compte lecteur créé.", "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    user = db.session.scalar(select(User).where(User.email == email))
    if not user or not bcrypt.check_password_hash(user.password_hash, password if isinstance(password, str) else ""):
        return jsonify({"success": False, "message": "E-mail ou mot de passe incorrect."}), 401
    if not user.is_active:
        return jsonify({"success": False, "message": "Ce compte est désactivé."}), 403

    claims = {"role": user.role, "email": user.email}
    return jsonify({
        "success": True,
        "user": user.to_dict(),
        "access_token": create_access_token(identity=str(user.id), additional_claims=claims),
        "refresh_token": create_refresh_token(identity=str(user.id), additional_claims=claims),
    }), 200


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user or not user.is_active:
        return jsonify({"success": False, "message": "Compte introuvable ou désactivé."}), 401
    return jsonify({
        "success": True,
        "access_token": create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role, "email": user.email},
        ),
    }), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user or not user.is_active:
        return jsonify({"success": False, "message": "Compte introuvable ou désactivé."}), 401
    return jsonify({"success": True, "user": user.to_dict()}), 200
