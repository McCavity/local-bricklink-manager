import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")

    # Database
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, "bricklink.db")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"

    # BrickLink API
    BRICKLINK_CONSUMER_KEY = os.getenv("BRICKLINK_CONSUMER_KEY", "")
    BRICKLINK_CONSUMER_SECRET = os.getenv("BRICKLINK_CONSUMER_SECRET", "")
    BRICKLINK_TOKEN = os.getenv("BRICKLINK_TOKEN", "")
    BRICKLINK_TOKEN_SECRET = os.getenv("BRICKLINK_TOKEN_SECRET", "")

    @property
    def bricklink_configured(self):
        return all([
            self.BRICKLINK_CONSUMER_KEY,
            self.BRICKLINK_CONSUMER_SECRET,
            self.BRICKLINK_TOKEN,
            self.BRICKLINK_TOKEN_SECRET,
        ])
