from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_

from .. import db
from ..models.comic import Comic
from ..models.interaction import UserComic

library_bp = Blueprint("library", __name__)


def _serialize_comic(comic: Comic):
    return {
        "id": comic.id,
        "source": comic.source,
        "source_id": comic.source_id,
        "title": comic.title,
        "author": comic.author,
        "publisher": comic.publisher,
        "genre": comic.genre,
        "year": comic.year,
        "rating": comic.rating,
        "description": comic.description,
        "tags": comic.tags or [],
        "cover_image": comic.cover_image,
    }


def _get_or_create_comic(payload: dict):
    comic_id = payload.get("comic_id")
    if comic_id:
        try:
            comic_id_int = int(comic_id)
        except (TypeError, ValueError):
            comic_id_int = None
        if comic_id_int is not None:
            return Comic.query.get(comic_id_int)

    data = payload.get("comic") or {}
    title = data.get("title")
    if not title:
        return None

    author = data.get("author")
    source_id = data.get("id") or data.get("source_id")
    existing = Comic.query.filter_by(title=title, author=author).first()
    if existing:
        # Backfill source mapping if it wasn't stored before.
        if source_id and not existing.source_id:
            existing.source_id = str(source_id)
            db.session.commit()
        return existing

    comic = Comic(
        source="catalog" if source_id else "custom",
        source_id=str(source_id) if source_id else None,
        title=title,
        author=author,
        publisher=data.get("publisher"),
        genre=data.get("genre"),
        year=data.get("year"),
        rating=data.get("rating") or 0.0,
        description=data.get("description"),
        tags=data.get("tags") or [],
        cover_image=data.get("cover_image"),
    )
    db.session.add(comic)
    db.session.commit()
    return comic


def _parse_user_id():
    raw = get_jwt_identity()
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _upsert_status(status: str):
    payload = request.get_json() or {}
    comic = _get_or_create_comic(payload)
    if not comic:
        return jsonify({"error": "Comic not found"}), 404

    user_id = _parse_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid token"}), 401

    # Ensure a single row per (user_id, comic_id) even if older DBs have duplicates.
    records = UserComic.query.filter_by(user_id=user_id, comic_id=comic.id).all()
    record = records[0] if records else None
    extras = records[1:] if len(records) > 1 else []

    if record is None:
        record = UserComic(
            user_id=user_id,
            comic_id=comic.id,
            status=status,
            rating=payload.get("rating"),
            notes=payload.get("notes"),
        )
        db.session.add(record)
    else:
        record.status = status
        record.rating = payload.get("rating", record.rating)
        record.notes = payload.get("notes", record.notes)

    for extra in extras:
        db.session.delete(extra)
    db.session.commit()

    return jsonify({"status": "ok", "comic": _serialize_comic(comic), "state": status})


def _get_by_status(status: str):
    user_id = _parse_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid token"}), 401
    records = UserComic.query.filter_by(user_id=user_id, status=status).all()
    comics = [Comic.query.get(record.comic_id) for record in records]
    return jsonify([_serialize_comic(comic) for comic in comics if comic])


@library_bp.post("/favorite")
@jwt_required()
def add_favorite():
    return _upsert_status("favorite")


@library_bp.post("/reading")
@jwt_required()
def add_reading():
    return _upsert_status("reading")


@library_bp.post("/complete")
@jwt_required()
def add_completed():
    return _upsert_status("completed")


@library_bp.post("/trash")
@jwt_required()
def add_trash():
    return _upsert_status("trash")


@library_bp.get("/favorites")
@jwt_required()
def favorites():
    return _get_by_status("favorite")


@library_bp.get("/reading")
@jwt_required()
def reading():
    return _get_by_status("reading")


@library_bp.get("/completed")
@jwt_required()
def completed():
    return _get_by_status("completed")


@library_bp.get("/trash")
@jwt_required()
def trash():
    user_id = _parse_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid token"}), 401
    query_text = (request.args.get("q") or "").strip()

    query = (
        db.session.query(Comic)
        .join(UserComic, UserComic.comic_id == Comic.id)
        .filter(UserComic.user_id == user_id, UserComic.status == "trash")
    )

    if query_text:
        like = f"%{query_text}%"
        query = query.filter(
            or_(
                Comic.title.ilike(like),
                Comic.author.ilike(like),
                Comic.genre.ilike(like),
            )
        )

    comics = query.all()
    return jsonify([_serialize_comic(comic) for comic in comics])


@library_bp.delete("/trash/<int:comic_id>")
@jwt_required()
def delete_trash(comic_id: int):
    user_id = _parse_user_id()
    if user_id is None:
        return jsonify({"error": "Invalid token"}), 401
    record = UserComic.query.filter_by(
        user_id=user_id, comic_id=comic_id, status="trash"
    ).first()
    if not record:
        return jsonify({"status": "not_found"}), 404
    db.session.delete(record)
    db.session.commit()
    return jsonify({"status": "deleted"})
