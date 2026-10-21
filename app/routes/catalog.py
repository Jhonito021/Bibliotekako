from flask import Blueprint, jsonify, request
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import Author, Book, Category, Publisher
from app.utils.security import roles_required

books_bp = Blueprint("books", __name__)
authors_bp = Blueprint("authors", __name__)
categories_bp = Blueprint("categories", __name__)
publishers_bp = Blueprint("publishers", __name__)

STAFF = ("admin", "librarian")


def _positive_int(value, field_name):
    try:
        result = int(value)
        if result < 1:
            raise ValueError
        return result
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} doit être un entier positif.")


@books_bp.get("")
def list_books():
    query = select(Book).where(Book.is_archived.is_(False))
    search = request.args.get("search", "").strip()
    category_id = request.args.get("category_id", type=int)
    year = request.args.get("year", type=int)
    if search:
        pattern = f"%{search}%"
        query = query.outerjoin(Book.authors).where(
            or_(Book.title.ilike(pattern), Book.isbn.ilike(pattern), Author.full_name.ilike(pattern))
        ).distinct()
    if category_id:
        query = query.where(Book.category_id == category_id)
    if year:
        query = query.where(Book.publication_year == year)

    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 10, type=int), 1), 100)
    pagination = db.paginate(query.order_by(Book.title.asc()), page=page, per_page=per_page, error_out=False)
    return jsonify({
        "success": True,
        "items": [book.to_dict() for book in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    }), 200


@books_bp.get("/<int:book_id>")
def get_book(book_id):
    book = db.session.get(Book, book_id)
    if not book or book.is_archived:
        return jsonify({"success": False, "message": "Livre introuvable."}), 404
    return jsonify({"success": True, "book": book.to_dict()}), 200


@books_bp.post("")
@roles_required(*STAFF)
def create_book():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify({"success": False, "message": "Le titre est obligatoire."}), 400

    try:
        category_id = _positive_int(data["category_id"], "category_id") if data.get("category_id") else None
        publisher_id = _positive_int(data["publisher_id"], "publisher_id") if data.get("publisher_id") else None
        author_ids = data.get("author_ids", [])
        if not isinstance(author_ids, list):
            raise ValueError("author_ids doit être une liste.")
        author_ids = [_positive_int(value, "author_ids") for value in author_ids]
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400

    category = db.session.get(Category, category_id) if category_id else None
    publisher = db.session.get(Publisher, publisher_id) if publisher_id else None
    authors = [db.session.get(Author, aid) for aid in author_ids]
    if category_id and not category:
        return jsonify({"success": False, "message": "Catégorie introuvable."}), 400
    if publisher_id and not publisher:
        return jsonify({"success": False, "message": "Éditeur introuvable."}), 400
    if any(author is None for author in authors):
        return jsonify({"success": False, "message": "Un ou plusieurs auteurs sont introuvables."}), 400

    year = data.get("publication_year")
    if year is not None and (not isinstance(year, int) or year < 0 or year > 2100):
        return jsonify({"success": False, "message": "publication_year invalide."}), 400

    book = Book(
        title=title,
        isbn=str(data.get("isbn", "")).strip() or None,
        description=data.get("description"),
        publication_year=year,
        cover_url=data.get("cover_url"),
        category=category,
        publisher=publisher,
        authors=authors,
    )
    db.session.add(book)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"success": False, "message": "Cet ISBN existe déjà."}), 409
    return jsonify({"success": True, "message": "Livre créé.", "book": book.to_dict()}), 201


@books_bp.put("/<int:book_id>")
@roles_required(*STAFF)
def update_book(book_id):
    book = db.session.get(Book, book_id)
    if not book or book.is_archived:
        return jsonify({"success": False, "message": "Livre introuvable."}), 404
    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = str(data["title"]).strip()
        if not title:
            return jsonify({"success": False, "message": "Le titre ne peut pas être vide."}), 400
        book.title = title
    if "isbn" in data:
        book.isbn = str(data["isbn"]).strip() or None
    if "description" in data:
        book.description = data["description"]
    if "cover_url" in data:
        book.cover_url = data["cover_url"]
    if "publication_year" in data:
        year = data["publication_year"]
        if year is not None and (not isinstance(year, int) or year < 0 or year > 2100):
            return jsonify({"success": False, "message": "publication_year invalide."}), 400
        book.publication_year = year
    for field, model, relationship in [
        ("category_id", Category, "category"),
        ("publisher_id", Publisher, "publisher"),
    ]:
        if field in data:
            if data[field] is None:
                setattr(book, relationship, None)
            else:
                try:
                    related_id = _positive_int(data[field], field)
                except ValueError as exc:
                    return jsonify({"success": False, "message": str(exc)}), 400
                related = db.session.get(model, related_id)
                if not related:
                    return jsonify({"success": False, "message": f"{relationship} introuvable."}), 400
                setattr(book, relationship, related)
    if "author_ids" in data:
        if not isinstance(data["author_ids"], list):
            return jsonify({"success": False, "message": "author_ids doit être une liste."}), 400
        try:
            ids = [_positive_int(value, "author_ids") for value in data["author_ids"]]
        except ValueError as exc:
            return jsonify({"success": False, "message": str(exc)}), 400
        authors = [db.session.get(Author, aid) for aid in ids]
        if any(author is None for author in authors):
            return jsonify({"success": False, "message": "Un ou plusieurs auteurs sont introuvables."}), 400
        book.authors = authors

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"success": False, "message": "ISBN déjà utilisé."}), 409
    return jsonify({"success": True, "message": "Livre modifié.", "book": book.to_dict()}), 200


@books_bp.delete("/<int:book_id>")
@roles_required(*STAFF)
def archive_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"success": False, "message": "Livre introuvable."}), 404
    book.is_archived = True
    db.session.commit()
    return jsonify({"success": True, "message": "Livre archivé."}), 200


def _list_entities(model, key):
    entities = db.session.scalars(select(model).order_by(model.id.asc())).all()
    return jsonify({"success": True, key: [entity.to_dict() for entity in entities]}), 200


def _create_named_entity(model, field, key):
    data = request.get_json(silent=True) or {}
    name = str(data.get(field, "")).strip()
    if not name:
        return jsonify({"success": False, "message": f"{field} est obligatoire."}), 400
    entity = model(**{field: name})
    if model is Author:
        entity.biography = data.get("biography")
    if model is Publisher:
        entity.address = data.get("address")
    if model is Category:
        entity.description = data.get("description")
    db.session.add(entity)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"success": False, "message": f"{field} existe déjà."}), 409
    return jsonify({"success": True, key: entity.to_dict()}), 201


@authors_bp.get("")
def list_authors():
    return _list_entities(Author, "authors")


@authors_bp.get("/<int:author_id>")
def get_author(author_id):
    author = db.session.get(Author, author_id)
    if not author:
        return jsonify({"success": False, "message": "Auteur introuvable."}), 404
    return jsonify({"success": True, "author": author.to_dict()}), 200


@authors_bp.post("")
@roles_required(*STAFF)
def create_author():
    return _create_named_entity(Author, "full_name", "author")


@categories_bp.get("")
def list_categories():
    return _list_entities(Category, "categories")


@categories_bp.get("/<int:category_id>")
def get_category(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        return jsonify({"success": False, "message": "Catégorie introuvable."}), 404
    return jsonify({"success": True, "category": category.to_dict()}), 200


@categories_bp.post("")
@roles_required(*STAFF)
def create_category():
    return _create_named_entity(Category, "name", "category")


@publishers_bp.get("")
def list_publishers():
    return _list_entities(Publisher, "publishers")


@publishers_bp.get("/<int:publisher_id>")
def get_publisher(publisher_id):
    publisher = db.session.get(Publisher, publisher_id)
    if not publisher:
        return jsonify({"success": False, "message": "Éditeur introuvable."}), 404
    return jsonify({"success": True, "publisher": publisher.to_dict()}), 200


@publishers_bp.post("")
@roles_required(*STAFF)
def create_publisher():
    return _create_named_entity(Publisher, "name", "publisher")
