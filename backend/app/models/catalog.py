from datetime import datetime, timezone
from backend.app.extensions import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


book_authors = db.Table(
    "book_authors",
    db.Column("book_id", db.Integer, db.ForeignKey("books.id"), primary_key=True),
    db.Column("author_id", db.Integer, db.ForeignKey("authors.id"), primary_key=True),
)


class Author(db.Model):
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(160), nullable=False, unique=True)
    biography = db.Column(db.Text)
    books = db.relationship("Book", secondary=book_authors, back_populates="authors")

    def to_dict(self):
        return {"id": self.id, "full_name": self.full_name, "biography": self.biography}


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    books = db.relationship("Book", back_populates="category")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description}


class Publisher(db.Model):
    __tablename__ = "publishers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, unique=True)
    address = db.Column(db.String(255))
    books = db.relationship("Book", back_populates="publisher")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "address": self.address}


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    isbn = db.Column(db.String(20), unique=True, nullable=True, index=True)
    description = db.Column(db.Text)
    publication_year = db.Column(db.Integer)
    cover_url = db.Column(db.String(500))
    is_archived = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    publisher_id = db.Column(db.Integer, db.ForeignKey("publishers.id"), nullable=True)

    category = db.relationship("Category", back_populates="books")
    publisher = db.relationship("Publisher", back_populates="books")
    authors = db.relationship("Author", secondary=book_authors, back_populates="books")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "isbn": self.isbn,
            "description": self.description,
            "publication_year": self.publication_year,
            "cover_url": self.cover_url,
            "is_archived": self.is_archived,
            "category": self.category.to_dict() if self.category else None,
            "publisher": self.publisher.to_dict() if self.publisher else None,
            "authors": [author.to_dict() for author in self.authors],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
