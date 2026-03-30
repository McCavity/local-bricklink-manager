import logging
import sqlite3
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
logger = logging.getLogger(__name__)


def _add_column_if_missing(conn, table, column, col_type, default=None):
    """Add a column to a table if it doesn't exist yet."""
    cursor = conn.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    if column not in existing:
        default_clause = ""
        if default is not None:
            default_clause = f" DEFAULT {default}"
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause}")
        logger.info(f"Added column {table}.{column}")


def _migrate(db_path):
    """Apply schema migrations for columns added after initial release."""
    try:
        conn = sqlite3.connect(db_path)
        # Check if the orders table exists at all
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='orders'"
        )
        if not cursor.fetchone():
            conn.close()
            return  # Fresh DB, create_all will handle everything

        _add_column_if_missing(conn, "orders", "subtotal_eur", "REAL")
        _add_column_if_missing(conn, "orders", "grand_total_eur", "REAL")
        _add_column_if_missing(conn, "orders", "shipping_cost_eur", "REAL")
        _add_column_if_missing(conn, "orders", "exchange_rate", "REAL")
        _add_column_if_missing(conn, "orders", "has_buyer_feedback", "BOOLEAN", "0")

        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Migration check failed: {e}")


def _backfill(db_path):
    """One-time backfill for existing orders that predate new columns."""
    try:
        conn = sqlite3.connect(db_path)

        # Auto-mark COMPLETED/PURGED/CANCELLED orders as checked if local_status is NULL
        conn.execute("""
            UPDATE orders SET local_status = 'checked'
            WHERE local_status IS NULL
            AND status IN ('COMPLETED', 'PURGED', 'CANCELLED')
        """)

        # Assume feedback was given for PURGED orders
        conn.execute("""
            UPDATE orders SET has_buyer_feedback = 1
            WHERE has_buyer_feedback = 0
            AND status = 'PURGED'
        """)

        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Backfill failed: {e}")


def init_db():
    from flask import current_app
    from app import models  # noqa: F401 — ensure models are registered

    # Run migrations before create_all (for existing DBs)
    db_path = current_app.config.get("DATABASE_PATH")
    if db_path:
        _migrate(db_path)
        _backfill(db_path)

    db.create_all()
