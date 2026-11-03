from .health import health_bp
from .auth import auth_bp
from .users import users_bp
from .catalog import books_bp, authors_bp, categories_bp, publishers_bp
from .extra import extra_bp


def register_routes(app):
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(books_bp, url_prefix="/api/books")
    app.register_blueprint(authors_bp, url_prefix="/api/authors")
    app.register_blueprint(categories_bp, url_prefix="/api/categories")
    app.register_blueprint(publishers_bp, url_prefix="/api/publishers")
    app.register_blueprint(extra_bp)
