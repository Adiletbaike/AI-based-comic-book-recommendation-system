from functools import lru_cache

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from ..ai.recommender import ComicRecommender, RecommenderConfig

recommend_bp = Blueprint("recommendations", __name__)

@lru_cache(maxsize=1)
def _get_recommender() -> ComicRecommender:
    cfg = RecommenderConfig(
        catalog_path=current_app.config["CATALOG_PATH"],
        index_dir=current_app.config["INDEX_DIR"],
        embedding_model=current_app.config["EMBEDDING_MODEL"],
        enable_reranker=bool(current_app.config.get("ENABLE_RERANKER")),
        rerank_model=current_app.config.get("RERANK_MODEL"),
        prompt_weight=float(current_app.config.get("PROMPT_WEIGHT") or 0.7),
        profile_weight=float(current_app.config.get("PROFILE_WEIGHT") or 0.3),
        cf_weight=float(current_app.config.get("CF_WEIGHT") or 0.0),
    )
    return ComicRecommender(cfg=cfg)


def _maybe_user_id() -> int | None:
    try:
        verify_jwt_in_request(optional=True)
        raw = get_jwt_identity()
        if raw is None:
            return None
        return int(raw)
    except Exception:
        return None


@recommend_bp.post("/chat")
def chat():
    payload = request.get_json() or {}
    prompt = payload.get("prompt", "")
    try:
        result = _get_recommender().process_prompt(prompt, user_id=_maybe_user_id())
        return jsonify(result)
    except Exception as e:
        # Make dependency issues diagnosable from the frontend.
        return (
            jsonify(
                {
                    "error": "recommender_init_failed",
                    "details": str(e),
                    "hint": "Check backend dependencies (transformers/sentence-transformers/torch) and EMBEDDING_MODEL.",
                }
            ),
            500,
        )


@recommend_bp.get("/popular")
def popular():
    recommender = _get_recommender()
    if recommender.comics_df.empty:
        return jsonify([])
    return jsonify(recommender.comics_df.head(10).to_dict("records"))


@recommend_bp.get("/personalized")
def personalized():
    recommender = _get_recommender()
    if recommender.comics_df.empty:
        return jsonify([])
    uid = _maybe_user_id()
    if uid is None:
        return jsonify({"error": "Unauthorized"}), 401
    recs, _ = recommender.recommend(prompt="", user_id=uid)
    return jsonify(recs)
