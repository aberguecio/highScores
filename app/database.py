"""Database configuration and helper functions"""

import os
import sqlite3
from typing import Optional
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

# Database configuration
DB_PATH = os.getenv("DB_PATH", "./data/highscores.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# SQLAlchemy setup (for Alembic migrations)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()


def get_db():
    """Get a database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_game_by_public_id(conn: sqlite3.Connection, public_id: str) -> Optional[sqlite3.Row]:
    """Fetch a game by its public ID"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM games WHERE public_id = ?", (public_id,))
    return cur.fetchone()
