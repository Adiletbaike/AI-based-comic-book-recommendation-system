from .. import db


class Comic(db.Model):
    __tablename__ = "comics"

    id = db.Column(db.Integer, primary_key=True)
    # Link back to catalog items so personalization can map interactions onto the full catalog.
    source = db.Column(db.String(50), default="catalog")
    source_id = db.Column(db.String(128), index=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255))
    publisher = db.Column(db.String(255))
    genre = db.Column(db.String(120))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)
    tags = db.Column(db.JSON, default=list)
    cover_image = db.Column(db.String(255))
