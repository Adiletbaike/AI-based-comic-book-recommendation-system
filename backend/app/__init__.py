from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

from .config import Config

db = SQLAlchemy()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)
    jwt.init_app(app)

    from .routes.auth import auth_bp
    from .routes.recommendations import recommend_bp
    from .routes.library import library_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(recommend_bp, url_prefix="/api/recommend")
    app.register_blueprint(library_bp, url_prefix="/api/library")

    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()

    return app
