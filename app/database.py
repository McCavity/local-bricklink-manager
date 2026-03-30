from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db():
    from app import models  # noqa: F401 — ensure models are registered
    db.create_all()
