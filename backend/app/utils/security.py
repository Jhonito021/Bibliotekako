from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def roles_required(*allowed_roles):
    def decorator(view_function):
        @wraps(view_function)
        def wrapped(*args, **kwargs):
            verify_jwt_in_request()
            role = get_jwt().get("role")
            if role not in allowed_roles:
                return jsonify({
                    "success": False,
                    "message": "Accès interdit pour ce rôle.",
                }), 403
            return view_function(*args, **kwargs)
        return wrapped
    return decorator
