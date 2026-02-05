import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-please-change-32-bytes-minimum")
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "dev-jwt-secret-please-change-32-bytes-minimum",
    )
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///comicai.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
