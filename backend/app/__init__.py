from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from pathlib import Path

db = SQLAlchemy()
jwt = JWTManager()


def create_app():
    # Load backend/.env if present (README expects this) even if the working directory is elsewhere.
    backend_env = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(backend_env, override=False)

    # Import config after dotenv is loaded so Config reads env vars correctly.
    from .config import Config

    app = Flask(__name__)
    app.config.from_object(Config)

    # Fail fast if secrets are missing (but allow local debug to run if explicitly set).
    if not app.config.get("SECRET_KEY") or not app.config.get("JWT_SECRET_KEY"):
        if app.config.get("DEBUG"):
            # Local-only: ephemeral secrets so the app can boot.
            # Tokens become invalid on restart, which is acceptable in debug.
            import secrets

            app.config["SECRET_KEY"] = app.config.get("SECRET_KEY") or secrets.token_hex(32)
            app.config["JWT_SECRET_KEY"] = app.config.get("JWT_SECRET_KEY") or secrets.token_hex(32)
        else:
            raise RuntimeError(
                "Missing SECRET_KEY/JWT_SECRET_KEY. Create backend/.env (see README) or set env vars."
            )

    origins = [
        o.strip()
        for o in (app.config.get("CORS_ORIGINS") or "").split(",")
        if o.strip()
    ]
    # Flask-CORS `resources` keys are regexes. `/api/*` does NOT match `/api/auth/...`;
    # use `/api/.*` to cover all API endpoints.
    CORS(
        app,
        resources={r"/api/.*": {"origins": origins or "*"}},
    )
    db.init_app(app)
    jwt.init_app(app)

    @app.before_request
    def _sanitize_bad_auth_header():
        # If the frontend ever sends "Bearer null"/"Bearer undefined" or a non-JWT token,
        # Flask-JWT-Extended returns 422. Strip it so the request behaves like unauthenticated (401).
        auth = request.headers.get("Authorization")
        if not auth:
            return None
        if not auth.lower().startswith("bearer "):
            return None
        token = auth[7:].strip()
        if not token:
            request.environ.pop("HTTP_AUTHORIZATION", None)
            return None
        if token in {"null", "undefined"} or token.count(".") != 2:
            request.environ.pop("HTTP_AUTHORIZATION", None)
        return None

    # JWT token revocation (logout) support.
    from .models.token import TokenBlocklist  # noqa: F401

    @jwt.token_in_blocklist_loader
    def _token_in_blocklist(jwt_header, jwt_payload):
        jti = jwt_payload.get("jti")
        if not jti:
            return True
        return db.session.query(TokenBlocklist.id).filter_by(jti=jti).first() is not None

    @jwt.revoked_token_loader
    def _revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has been revoked"}), 401

    @jwt.invalid_token_loader
    def _invalid_token_callback(reason: str):
        # By default some invalid token cases return 422. Normalize to 401 so the frontend
        # treats it like an unauthenticated session and can recover.
        return jsonify({"error": "Invalid token"}), 401

    @jwt.unauthorized_loader
    def _missing_token_callback(reason: str):
        return jsonify({"error": "Missing Authorization Header"}), 401

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
