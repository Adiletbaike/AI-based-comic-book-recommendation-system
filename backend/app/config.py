import os
from pathlib import Path


class Config:
    # Security: do not ship/run with known default secrets.
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    # Flask/Runtime
    DEBUG = os.getenv("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
    PORT = int(os.getenv("PORT", "5001"))

    # CORS: comma-separated allowlist, defaulting to local dev origins.
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )

    # Database
    _backend_dir = Path(__file__).resolve().parents[1]  # backend/
    _default_sqlite_path = _backend_dir / "comicai.db"
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{_default_sqlite_path}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Password reset tokens
    RESET_TOKEN_TTL_SECONDS = int(os.getenv("RESET_TOKEN_TTL_SECONDS", "3600"))
    RETURN_RESET_TOKEN = os.getenv("RETURN_RESET_TOKEN", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    # Recommender settings
    CATALOG_PATH = os.getenv(
        "CATALOG_PATH",
        str((Path(__file__).resolve().parents[1] / "data" / "books_manga_comics_catalog.csv")),
    )
    INDEX_DIR = os.getenv(
        "INDEX_DIR",
        str((Path(__file__).resolve().parents[1] / "data")),
    )
    # Default kept conservative for compatibility on common dev machines.
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    ENABLE_RERANKER = os.getenv("ENABLE_RERANKER", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    RERANK_MODEL = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

    # Blend weights (prompt vs personalization). 1.0 means prompt-only.
    PROMPT_WEIGHT = float(os.getenv("PROMPT_WEIGHT", "0.7"))
    PROFILE_WEIGHT = float(os.getenv("PROFILE_WEIGHT", "0.3"))
    CF_WEIGHT = float(os.getenv("CF_WEIGHT", "0.0"))
