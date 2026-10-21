from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func
from app.extensions import db
from app.models import User, Book, BookCopy, Loan, Reservation, Fine, Notification, AuditLog, AppSetting
from app.utils.security import roles_required

extra_bp = Blueprint("extra", __name__)
STAFF = ("admin", "librarian")
COPY_STATUSES = {"available", "borrowed", "reserved", "damaged", "lost"}

def _err(message, code=400):
    return jsonify({"success": False, "error": message}), code

def _uid():
    try: return int(get_jwt_identity())
    except (TypeError, ValueError): return None

def _audit(action, entity, entity_id=None, details=None):
    db.session.add(AuditLog(actor_id=_uid(), action=action, entity_type=entity,
                            entity_id=entity_id, details=details or {}))

def _notify(user_id, title, message, kind="info"):
    db.session.add(Notification(user_id=user_id, title=title, message=message, kind=kind))

def _owner_or_staff(owner_id):
    return int(owner_id) == _uid() or get_jwt().get("role") in STAFF

# Copies
@extra_bp.get("/api/copies")
@roles_required(*STAFF)
def copies_list():
    q = BookCopy.query
    if request.args.get("book_id", type=int): q = q.filter_by(book_id=request.args.get("book_id", type=int))
    if request.args.get("status"): q = q.filter_by(status=request.args["status"])
    return jsonify({"items": [x.to_dict() for x in q.order_by(BookCopy.id.desc()).all()]})

@extra_bp.get("/api/copies/<int:copy_id>")
@roles_required(*STAFF)
def copy_detail(copy_id):
    x = db.session.get(BookCopy, copy_id)
    return (jsonify({"copy": x.to_dict()}), 200) if x else _err("Exemplaire introuvable", 404)

@extra_bp.get("/api/books/<int:book_id>/copies")
def book_copies(book_id):
    book = db.session.get(Book, book_id)
    if not book or book.is_archived: return _err("Livre introuvable", 404)
    return jsonify({"items": [x.to_dict() for x in BookCopy.query.filter_by(book_id=book_id).all()]})

@extra_bp.post("/api/copies")
@roles_required(*STAFF)
def copy_create():
    d = request.get_json(silent=True) or {}
    try: book_id = int(d.get("book_id"))
    except (TypeError, ValueError): return _err("book_id est obligatoire et doit être numérique")
    code = str(d.get("inventory_code", "")).strip()
    status = d.get("status", "available")
    book = db.session.get(Book, book_id)
    if not book or book.is_archived: return _err("Livre introuvable", 404)
    if not code: return _err("inventory_code est obligatoire")
    if BookCopy.query.filter_by(inventory_code=code).first(): return _err("Code inventaire déjà utilisé", 409)
    if status not in COPY_STATUSES: return _err("Statut invalide")
    x = BookCopy(book_id=book_id, inventory_code=code, status=status, condition_note=d.get("condition_note"))
    db.session.add(x); db.session.flush(); _audit("copy.created", "copy", x.id, {"inventory_code": code}); db.session.commit()
    return jsonify({"copy": x.to_dict()}), 201

@extra_bp.put("/api/copies/<int:copy_id>")
@extra_bp.patch("/api/copies/<int:copy_id>/status")
@roles_required(*STAFF)
def copy_update(copy_id):
    x = db.session.get(BookCopy, copy_id)
    if not x: return _err("Exemplaire introuvable", 404)
    d = request.get_json(silent=True) or {}
    if request.path.endswith("/status") and "status" not in d: return _err("status est obligatoire")
    if "inventory_code" in d:
        code = str(d["inventory_code"]).strip()
        duplicate = BookCopy.query.filter(BookCopy.inventory_code == code, BookCopy.id != x.id).first()
        if not code or duplicate: return _err("Code inventaire vide ou déjà utilisé", 409)
        x.inventory_code = code
    if "condition_note" in d: x.condition_note = d["condition_note"]
    if "status" in d:
        if d["status"] not in COPY_STATUSES: return _err("Statut invalide")
        if Loan.query.filter_by(copy_id=x.id, status="active").first() and d["status"] != "borrowed":
            return _err("Cet exemplaire est actuellement emprunté", 409)
        x.status = d["status"]
    _audit("copy.updated", "copy", x.id, {"fields": list(d.keys())}); db.session.commit()
    return jsonify({"copy": x.to_dict()})

# Loans
@extra_bp.get("/api/loans")
@roles_required(*STAFF)
def loans_list():
    q = Loan.query
    if request.args.get("status"): q = q.filter_by(status=request.args["status"])
    if request.args.get("reader_id", type=int): q = q.filter_by(reader_id=request.args.get("reader_id", type=int))
    return jsonify({"items": [x.to_dict() for x in q.order_by(Loan.id.desc()).all()]})

@extra_bp.get("/api/loans/overdue")
@roles_required(*STAFF)
def loans_overdue():
    items = Loan.query.filter(Loan.status == "active", Loan.due_at < datetime.utcnow()).all()
    return jsonify({"items": [x.to_dict() for x in items]})

@extra_bp.get("/api/loans/<int:loan_id>")
@jwt_required()
def loan_detail(loan_id):
    x = db.session.get(Loan, loan_id)
    if not x: return _err("Emprunt introuvable", 404)
    if not _owner_or_staff(x.reader_id): return _err("Accès interdit", 403)
    return jsonify({"loan": x.to_dict()})

@extra_bp.post("/api/loans")
@roles_required(*STAFF)
def loan_create():
    d = request.get_json(silent=True) or {}
    try: reader_id, copy_id = int(d.get("reader_id")), int(d.get("copy_id"))
    except (TypeError, ValueError): return _err("reader_id et copy_id sont obligatoires")
    reader, copy = db.session.get(User, reader_id), db.session.get(BookCopy, copy_id)
    if not reader or reader.role != "reader" or not reader.is_active: return _err("Lecteur absent, inactif ou non autorisé", 409)
    if not copy or copy.status != "available" or not copy.book or copy.book.is_archived: return _err("Exemplaire indisponible", 409)
    active = Loan.query.filter_by(reader_id=reader_id, status="active").count()
    if active >= int(current_app.config.get("MAX_ACTIVE_LOANS", 5)): return _err("Nombre maximal d'emprunts atteint", 409)
    # Recheck active loan for this copy; the transaction prevents ordinary duplicate requests.
    if Loan.query.filter_by(copy_id=copy_id, status="active").first(): return _err("Exemplaire déjà emprunté", 409)
    days = int(current_app.config.get("LOAN_DURATION_DAYS", 14))
    x = Loan(reader_id=reader_id, copy_id=copy_id, due_at=datetime.utcnow()+timedelta(days=days), created_by=_uid())
    copy.status = "borrowed"; db.session.add(x); db.session.flush()
    _notify(reader_id, "Nouvel emprunt", f"Date limite de retour : {x.due_at:%Y-%m-%d}.", "loan")
    _audit("loan.created", "loan", x.id, {"reader_id": reader_id, "copy_id": copy_id})
    db.session.commit(); return jsonify({"loan": x.to_dict()}), 201

@extra_bp.post("/api/loans/<int:loan_id>/return")
@roles_required(*STAFF)
def loan_return(loan_id):
    x = db.session.get(Loan, loan_id)
    if not x: return _err("Emprunt introuvable", 404)
    if x.status != "active": return _err("Emprunt déjà clôturé", 409)
    now = datetime.utcnow(); x.returned_at = now; x.status = "returned"
    if x.copy: x.copy.status = "available"
    days_late = max(0, (now - x.due_at).days)
    fine = None
    if days_late:
        fine = Fine(loan_id=x.id, reader_id=x.reader_id,
                    amount=days_late * int(current_app.config.get("FINE_PER_DAY", 500)),
                    reason=f"Retard de {days_late} jour(s)")
        db.session.add(fine); _notify(x.reader_id, "Pénalité de retard", f"Une pénalité de {fine.amount} a été créée.", "fine")
    _notify(x.reader_id, "Retour enregistré", "Le retour de votre livre est enregistré.", "loan")
    _audit("loan.returned", "loan", x.id, {"overdue_days": days_late}); db.session.commit()
    return jsonify({"loan": x.to_dict(), "fine": fine.to_dict() if fine else None})

@extra_bp.patch("/api/loans/<int:loan_id>/extend")
@roles_required(*STAFF)
def loan_extend(loan_id):
    x = db.session.get(Loan, loan_id)
    if not x: return _err("Emprunt introuvable", 404)
    if x.status != "active" or x.due_at < datetime.utcnow(): return _err("Emprunt non prolongeable", 409)
    x.due_at += timedelta(days=int(current_app.config.get("LOAN_DURATION_DAYS", 14)))
    _notify(x.reader_id, "Emprunt prolongé", f"Nouvelle échéance : {x.due_at:%Y-%m-%d}.", "loan")
    _audit("loan.extended", "loan", x.id); db.session.commit(); return jsonify({"loan": x.to_dict()})

@extra_bp.get("/api/me/loans")
@jwt_required()
def my_loans():
    uid = _uid(); history = request.args.get("history") == "true"
    status = "returned" if history else "active"
    return jsonify({"items": [x.to_dict() for x in Loan.query.filter_by(reader_id=uid, status=status).order_by(Loan.id.desc()).all()]})

@extra_bp.get("/api/me/loans/history")
@jwt_required()
def my_loan_history():
    return jsonify({"items": [x.to_dict() for x in Loan.query.filter_by(reader_id=_uid(), status="returned").order_by(Loan.id.desc()).all()]})

# Reservations
@extra_bp.get("/api/reservations")
@roles_required(*STAFF)
def reservations_list():
    q = Reservation.query
    if request.args.get("status"): q = q.filter_by(status=request.args["status"])
    return jsonify({"items": [x.to_dict() for x in q.order_by(Reservation.id.desc()).all()]})

@extra_bp.get("/api/reservations/<int:reservation_id>")
@jwt_required()
def reservation_detail(reservation_id):
    x = db.session.get(Reservation, reservation_id)
    if not x: return _err("Réservation introuvable", 404)
    if not _owner_or_staff(x.reader_id): return _err("Accès interdit", 403)
    return jsonify({"reservation": x.to_dict()})

@extra_bp.post("/api/reservations")
@jwt_required()
def reservation_create():
    d = request.get_json(silent=True) or {}
    try: book_id = int(d.get("book_id"))
    except (TypeError, ValueError): return _err("book_id est obligatoire")
    book = db.session.get(Book, book_id)
    if not book or book.is_archived: return _err("Livre introuvable", 404)
    uid = _uid()
    if Reservation.query.filter_by(reader_id=uid, book_id=book_id, status="waiting").first(): return _err("Réservation déjà active", 409)
    if BookCopy.query.filter_by(book_id=book_id, status="available").first(): return _err("Un exemplaire est disponible", 409)
    x = Reservation(reader_id=uid, book_id=book_id); db.session.add(x); db.session.flush()
    _audit("reservation.created", "reservation", x.id, {"book_id": book_id}); db.session.commit()
    return jsonify({"reservation": x.to_dict()}), 201

@extra_bp.get("/api/me/reservations")
@jwt_required()
def my_reservations():
    return jsonify({"items": [x.to_dict() for x in Reservation.query.filter_by(reader_id=_uid()).order_by(Reservation.id.desc()).all()]})

@extra_bp.post("/api/reservations/<int:reservation_id>/cancel")
@jwt_required()
def reservation_cancel(reservation_id):
    x = db.session.get(Reservation, reservation_id)
    if not x: return _err("Réservation introuvable", 404)
    if not _owner_or_staff(x.reader_id): return _err("Accès interdit", 403)
    if x.status not in ("waiting", "ready"): return _err("Réservation non annulable", 409)
    x.status = "cancelled"; _audit("reservation.cancelled", "reservation", x.id); db.session.commit()
    return jsonify({"reservation": x.to_dict()})

@extra_bp.patch("/api/reservations/<int:reservation_id>/status")
@roles_required(*STAFF)
def reservation_status(reservation_id):
    x = db.session.get(Reservation, reservation_id)
    if not x: return _err("Réservation introuvable", 404)
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in {"waiting", "ready", "fulfilled", "cancelled", "expired"}: return _err("Statut invalide")
    x.status = status
    if status == "ready":
        x.expires_at = datetime.utcnow() + timedelta(days=int(current_app.config.get("RESERVATION_HOLD_DAYS", 2)))
        _notify(x.reader_id, "Livre disponible", f"Le livre « {x.book.title} » est disponible.", "reservation")
    _audit("reservation.status_updated", "reservation", x.id, {"status": status}); db.session.commit()
    return jsonify({"reservation": x.to_dict()})

# Fines
@extra_bp.get("/api/fines")
@roles_required(*STAFF)
def fines_list():
    q = Fine.query
    if request.args.get("status"): q = q.filter_by(status=request.args["status"])
    return jsonify({"items": [x.to_dict() for x in q.order_by(Fine.id.desc()).all()]})

@extra_bp.get("/api/fines/<int:fine_id>")
@jwt_required()
def fine_detail(fine_id):
    x = db.session.get(Fine, fine_id)
    if not x: return _err("Pénalité introuvable", 404)
    if not _owner_or_staff(x.reader_id): return _err("Accès interdit", 403)
    return jsonify({"fine": x.to_dict()})

@extra_bp.get("/api/me/fines")
@jwt_required()
def my_fines():
    return jsonify({"items": [x.to_dict() for x in Fine.query.filter_by(reader_id=_uid()).order_by(Fine.id.desc()).all()]})

@extra_bp.post("/api/fines/<int:fine_id>/payment")
@roles_required(*STAFF)
def fine_payment(fine_id):
    x = db.session.get(Fine, fine_id)
    if not x: return _err("Pénalité introuvable", 404)
    if x.status != "unpaid": return _err("Pénalité déjà traitée", 409)
    x.status = "paid"; x.paid_at = datetime.utcnow()
    _notify(x.reader_id, "Pénalité réglée", f"Règlement enregistré : {x.amount}.", "fine")
    _audit("fine.paid", "fine", x.id, {"amount": x.amount}); db.session.commit()
    return jsonify({"fine": x.to_dict()})

@extra_bp.post("/api/fines/<int:fine_id>/waive")
@roles_required("admin")
def fine_waive(fine_id):
    x = db.session.get(Fine, fine_id)
    if not x: return _err("Pénalité introuvable", 404)
    if x.status != "unpaid": return _err("Pénalité déjà traitée", 409)
    x.status = "waived"; x.waived_at = datetime.utcnow()
    _notify(x.reader_id, "Pénalité annulée", "L'administration a dispensé cette pénalité.", "fine")
    _audit("fine.waived", "fine", x.id); db.session.commit(); return jsonify({"fine": x.to_dict()})

# Notifications
@extra_bp.get("/api/notifications")
@jwt_required()
def notifications_list():
    items = Notification.query.filter_by(user_id=_uid()).order_by(Notification.id.desc()).all()
    return jsonify({"items": [x.to_dict() for x in items]})

@extra_bp.get("/api/notifications/unread-count")
@jwt_required()
def notifications_unread():
    return jsonify({"count": Notification.query.filter_by(user_id=_uid(), is_read=False).count()})

@extra_bp.patch("/api/notifications/read-all")
@jwt_required()
def notifications_read_all():
    Notification.query.filter_by(user_id=_uid(), is_read=False).update({"is_read": True})
    db.session.commit(); return jsonify({"message": "Notifications marquées comme lues"})

@extra_bp.patch("/api/notifications/<int:notification_id>/read")
@jwt_required()
def notification_read(notification_id):
    x = db.session.get(Notification, notification_id)
    if not x or x.user_id != _uid(): return _err("Notification introuvable", 404)
    x.is_read = True; db.session.commit(); return jsonify({"notification": x.to_dict()})

# Profile
@extra_bp.put("/api/me")
@jwt_required()
def profile_update():
    x = db.session.get(User, _uid())
    if not x: return _err("Utilisateur introuvable", 404)
    d = request.get_json(silent=True) or {}
    if "full_name" in d:
        name = str(d["full_name"]).strip()
        if not name: return _err("Nom invalide")
        x.full_name = name
    if "email" in d:
        email = str(d["email"]).strip().lower()
        if not email: return _err("E-mail invalide")
        if User.query.filter(User.email == email, User.id != x.id).first(): return _err("E-mail déjà utilisé", 409)
        x.email = email
    db.session.commit(); return jsonify({"user": x.to_dict()})

@extra_bp.patch("/api/me/password")
@jwt_required()
def profile_password():
    from app.extensions import bcrypt
    x = db.session.get(User, _uid()); d = request.get_json(silent=True) or {}
    if not x: return _err("Utilisateur introuvable", 404)
    if not bcrypt.check_password_hash(x.password_hash, str(d.get("current_password", ""))): return _err("Mot de passe actuel incorrect", 401)
    new = str(d.get("new_password", ""))
    if len(new) < 8: return _err("Le nouveau mot de passe doit contenir au moins 8 caractères")
    x.password_hash = bcrypt.generate_password_hash(new).decode("utf-8"); db.session.commit()
    return jsonify({"message": "Mot de passe modifié"})

# Dashboard
@extra_bp.get("/api/dashboard")
@roles_required(*STAFF)
def dashboard():
    now = datetime.utcnow()
    return jsonify({"titles": Book.query.filter_by(is_archived=False).count(),
        "copies": BookCopy.query.count(), "available_copies": BookCopy.query.filter_by(status="available").count(),
        "active_readers": User.query.filter_by(role="reader", is_active=True).count(),
        "active_loans": Loan.query.filter_by(status="active").count(),
        "returned_loans": Loan.query.filter_by(status="returned").count(),
        "overdue_loans": Loan.query.filter(Loan.status == "active", Loan.due_at < now).count(),
        "unpaid_fines": db.session.query(func.coalesce(func.sum(Fine.amount), 0)).filter_by(status="unpaid").scalar()})

@extra_bp.get("/api/dashboard/loans")
@extra_bp.get("/api/dashboard/monthly")
@roles_required(*STAFF)
def dashboard_monthly():
    year = request.args.get("year", str(datetime.utcnow().year), type=int)
    rows = db.session.query(func.month(Loan.borrowed_at), func.count(Loan.id)).filter(
        func.year(Loan.borrowed_at) == year).group_by(func.month(Loan.borrowed_at)).order_by(func.month(Loan.borrowed_at)).all()
    return jsonify({"year": year, "monthly": [{"month": int(m), "count": int(c)} for m, c in rows]})

@extra_bp.get("/api/dashboard/overdue")
@roles_required(*STAFF)
def dashboard_overdue():
    items = Loan.query.filter(Loan.status == "active", Loan.due_at < datetime.utcnow()).order_by(Loan.due_at).all()
    return jsonify({"count": len(items), "items": [x.to_dict() for x in items]})

@extra_bp.get("/api/dashboard/popular-books")
@roles_required(*STAFF)
def dashboard_popular():
    rows = db.session.query(Book.id, Book.title, func.count(Loan.id).label("total")).join(
        BookCopy, BookCopy.book_id == Book.id).join(Loan, Loan.copy_id == BookCopy.id).group_by(
        Book.id, Book.title).order_by(func.count(Loan.id).desc()).limit(10).all()
    return jsonify({"items": [{"book_id": r.id, "title": r.title, "loan_count": int(r.total)} for r in rows]})

@extra_bp.get("/api/dashboard/yearly")
@roles_required(*STAFF)
def dashboard_yearly():
    rows = db.session.query(func.year(Loan.borrowed_at)).distinct().order_by(func.year(Loan.borrowed_at).desc()).all()
    return jsonify({"years": [int(r[0]) for r in rows if r[0] is not None]})

# Audit and settings
@extra_bp.get("/api/audit-logs")
@roles_required("admin")
def audit_list():
    try: limit = min(100, max(1, int(request.args.get("limit", 50))))
    except ValueError: limit = 50
    q = AuditLog.query
    if request.args.get("action"): q = q.filter_by(action=request.args["action"])
    return jsonify({"items": [x.to_dict() for x in q.order_by(AuditLog.id.desc()).limit(limit).all()]})

@extra_bp.get("/api/audit-logs/<int:log_id>")
@roles_required("admin")
def audit_detail(log_id):
    x = db.session.get(AuditLog, log_id)
    return (jsonify({"item": x.to_dict()}), 200) if x else _err("Journal introuvable", 404)

@extra_bp.get("/api/settings")
@roles_required(*STAFF)
def settings_list():
    values = {"loan_duration_days": "14", "max_active_loans": "5", "fine_per_day": "500", "reservation_hold_days": "2"}
    values.update({x.key: x.value for x in AppSetting.query.all()})
    return jsonify({"settings": values})

@extra_bp.put("/api/settings")
@roles_required("admin")
def settings_update():
    d = request.get_json(silent=True) or {}
    allowed = {"loan_duration_days", "max_active_loans", "fine_per_day", "reservation_hold_days"}
    if not d or set(d) - allowed: return _err("Paramètres invalides")
    for key, value in d.items():
        try: n = int(value)
        except (TypeError, ValueError): return _err(f"{key} doit être numérique")
        if n < 0 or (key != "fine_per_day" and n == 0): return _err(f"Valeur invalide pour {key}")
        item = AppSetting.query.filter_by(key=key).first()
        if item: item.value = str(n)
        else: db.session.add(AppSetting(key=key, value=str(n)))
    _audit("settings.updated", "settings", details={"keys": list(d)})
    db.session.commit(); return jsonify({"settings": {x.key: x.value for x in AppSetting.query.all()}})
