"""Authentication and authorization functions"""

import os
import secrets
import sqlite3
from typing import Optional
from fastapi import HTTPException, Header

from .database import get_game_by_public_id

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "change-me")


def generate_api_key() -> str:
    """Generate a secure random API key"""
    return "sk_" + secrets.token_urlsafe(32)


def require_admin_token(x_admin_token: str = Header(None, alias="X-Admin-Token")):
    """Dependency to require admin authentication"""
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid admin token")


def verify_game_ownership_or_admin(
    conn: sqlite3.Connection,
    public_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")
) -> sqlite3.Row:
    """
    Verify that the request is either from the game owner (via API key) or an admin.
    Returns the game row if authorized, raises HTTPException otherwise.
    """
    game = get_game_by_public_id(conn, public_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Check if admin token is valid
    if x_admin_token == ADMIN_TOKEN:
        return game

    # Check if API key matches the game's API key
    if x_api_key and x_api_key == game["api_key"]:
        return game

    raise HTTPException(
        status_code=403,
        detail="Unauthorized. Provide valid X-API-Key (game owner) or X-Admin-Token (admin)"
    )
