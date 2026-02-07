import hashlib
import hmac
import secrets
from datetime import timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from .. import db
from ..models.token import PasswordResetToken, TokenBlocklist
from ..models.user import User
from ..utils.helpers import utc_now

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    payload = request.get_json() or {}
    username = payload.get("username")
    email = payload.get("email")
    password = payload.get("password")
    if not username or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify(
        {
            "access_token": token,
            "user": {"id": user.id, "username": user.username, "email": user.email},
        }
    )


@auth_bp.post("/login")
def login():
    payload = request.get_json() or {}
    email = payload.get("email")
    password = payload.get("password")
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify(
        {
            "access_token": token,
            "user": {"id": user.id, "username": user.username, "email": user.email},
        }
    )


def _hash_reset_token(raw_token: str) -> str:
    # Store only a keyed hash of the token so DB leaks don't become account takeovers.
    secret = (current_app.config.get("SECRET_KEY") or "").encode("utf-8")
    msg = raw_token.encode("utf-8")
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()


@auth_bp.post("/forgot-password")
def forgot_password():
    payload = request.get_json() or {}
    email = (payload.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "Missing email"}), 400

    # Always return "ok" to avoid leaking which emails exist.
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"status": "ok"})

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_reset_token(raw_token)

    ttl = int(current_app.config.get("RESET_TOKEN_TTL_SECONDS") or 3600)
    expires_at = utc_now() + timedelta(seconds=ttl)

    rec = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        used_at=None,
    )
    db.session.add(rec)
    db.session.commit()

    resp = {"status": "ok"}
    if current_app.config.get("DEBUG") or current_app.config.get("RETURN_RESET_TOKEN"):
        # Dev-only convenience. Production should email this token.
        resp["reset_token"] = raw_token
        resp["expires_at"] = expires_at.isoformat() + "Z"
    return jsonify(resp)


@auth_bp.post("/reset-password")
def reset_password():
    payload = request.get_json() or {}
    raw_token = (payload.get("token") or "").strip()
    new_password = payload.get("new_password") or payload.get("password") or ""
    if not raw_token or not new_password:
        return jsonify({"error": "Missing token or new_password"}), 400
    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    token_hash = _hash_reset_token(raw_token)
    rec = PasswordResetToken.query.filter_by(token_hash=token_hash).first()
    if not rec or rec.used_at is not None:
        return jsonify({"error": "Invalid token"}), 400
    if rec.expires_at < utc_now():
        return jsonify({"error": "Token expired"}), 400

    user = User.query.get(rec.user_id)
    if not user:
        return jsonify({"error": "Invalid token"}), 400

    user.password_hash = generate_password_hash(new_password)
    rec.used_at = utc_now()
    db.session.commit()
    return jsonify({"status": "ok"})


@auth_bp.post("/logout")
@jwt_required()
def logout():
    # JWTs are stateless; logout is implemented by revoking the current token's JTI.
    # Frontend should also discard its local copy.
    jti = (get_jwt() or {}).get("jti")
    if not jti:
        return jsonify({"error": "Invalid token"}), 401

    user_id = None
    try:
        # identity is a stringified user id in this app
        from flask_jwt_extended import get_jwt_identity

        raw = get_jwt_identity()
        user_id = int(raw) if raw is not None else None
    except Exception:
        user_id = None

    exists = TokenBlocklist.query.filter_by(jti=jti).first()
    if not exists:
        db.session.add(TokenBlocklist(jti=jti, user_id=user_id))
        db.session.commit()
    return jsonify({"status": "ok"})
