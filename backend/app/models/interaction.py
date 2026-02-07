from .. import db
from ..utils.helpers import utc_now


class UserComic(db.Model):
    __tablename__ = "user_comics"
    __table_args__ = (
        db.UniqueConstraint("user_id", "comic_id", name="uq_user_comic"),
        db.Index("ix_user_comics_user_status", "user_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    comic_id = db.Column(db.Integer, db.ForeignKey("comics.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    rating = db.Column(db.Float)
    notes = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
