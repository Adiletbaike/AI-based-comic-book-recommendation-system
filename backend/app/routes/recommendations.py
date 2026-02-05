import os

from flask import Blueprint, jsonify, request

from ..ai.recommender import ComicRecommender

recommend_bp = Blueprint("recommendations", __name__)

DATASET_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "books_manga_comics_catalog.csv"
)
EMBEDDINGS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "embeddings.npy")

recommender = ComicRecommender(dataset_path=DATASET_PATH, embeddings_path=EMBEDDINGS_PATH)


@recommend_bp.post("/chat")
def chat():
    payload = request.get_json() or {}
    prompt = payload.get("prompt", "")
    result = recommender.process_prompt(prompt)
    return jsonify(result)


@recommend_bp.get("/popular")
def popular():
    if recommender.comics_df.empty:
        return jsonify([])
    return jsonify(recommender.comics_df.head(10).to_dict("records"))


@recommend_bp.get("/personalized")
def personalized():
    if recommender.comics_df.empty:
        return jsonify([])
    return jsonify(recommender.comics_df.sample(min(10, len(recommender.comics_df))).to_dict("records"))
