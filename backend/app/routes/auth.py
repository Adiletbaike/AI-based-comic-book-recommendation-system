from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from .. import db
from ..models.user import User

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


@auth_bp.post("/forgot-password")
def forgot_password():
    return jsonify({"status": "ok"})


@auth_bp.post("/reset-password")
def reset_password():
    return jsonify({"status": "ok"})


@auth_bp.post("/logout")
def logout():
    return jsonify({"status": "ok"})
