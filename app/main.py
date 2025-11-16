"""Main FastAPI application"""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    GameCreate, GameOut, GameInfo,
    HighscoreIn, HighscoreOut, HighscoreList
)
from .database import get_db, get_game_by_public_id
from .auth import (
    generate_api_key,
    require_admin_token,
    verify_game_ownership_or_admin
)

app = FastAPI(
    title="Highscores API",
    description="A lightweight REST API for managing game leaderboards",
    version="2.0.0"
)

# Configure CORS - Allow all origins for public API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)


# ========== ENDPOINTS ==========

@app.get("/")
def healthcheck():
    """Health check endpoint"""
    return {"status": "ok", "version": "2.0.0"}


# ---------- PUBLIC: Create game ----------

@app.post("/games", response_model=GameOut, status_code=201)
def create_game(game: GameCreate):
    """
    Public: Anyone can create a new game.
    Returns public_id and api_key. Save the api_key - you'll need it to manage your game.
    """
    conn = get_db()
    cur = conn.cursor()

    public_id = "g_" + uuid.uuid4().hex[:16]
    api_key = generate_api_key()
    now = datetime.utcnow().isoformat()

    try:
        cur.execute(
            "INSERT INTO games (public_id, name, email, api_key, created_at) VALUES (?, ?, ?, ?, ?)",
            (public_id, game.name.strip(), game.email.lower(), api_key, now)
        )
        conn.commit()
    finally:
        conn.close()

    return GameOut(
        public_id=public_id,
        name=game.name.strip(),
        email=game.email.lower(),
        api_key=api_key,
        created_at=now
    )


# ---------- PUBLIC: Submit highscore ----------

@app.post(
    "/games/{public_id}/highscores",
    response_model=HighscoreOut,
    status_code=201
)
def submit_highscore(public_id: str, hs: HighscoreIn):
    """
    Public: Submit a new highscore for a game.
    """
    conn = get_db()
    try:
        game = get_game_by_public_id(conn, public_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        now = datetime.utcnow().isoformat()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO highscores (game_id, player_name, score, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (game["id"], hs.player_name.strip(), int(hs.score), now)
        )
        conn.commit()
    finally:
        conn.close()

    return HighscoreOut(
        player_name=hs.player_name.strip(),
        score=int(hs.score),
        created_at=now
    )


# ---------- PUBLIC: Get highscores ----------

@app.get(
    "/games/{public_id}/highscores",
    response_model=HighscoreList
)
def get_highscores(
    public_id: str,
    limit: int = Query(10, ge=1, le=50)
):
    """
    Public: Get the top N highscores for a game.
    """
    conn = get_db()
    try:
        game = get_game_by_public_id(conn, public_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        cur = conn.cursor()
        cur.execute(
            """
            SELECT player_name, score, created_at
            FROM highscores
            WHERE game_id = ?
            ORDER BY score DESC, created_at ASC
            LIMIT ?
            """,
            (game["id"], limit)
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    highscores = [
        HighscoreOut(
            player_name=row["player_name"],
            score=row["score"],
            created_at=row["created_at"]
        )
        for row in rows
    ]

    return HighscoreList(game_id=public_id, highscores=highscores)


# ---------- ADMIN: List games ----------

@app.get("/games", response_model=List[GameInfo])
def list_games(x_admin_token: str = Header(None, alias="X-Admin-Token")):
    """
    Admin only: List all games (requires X-Admin-Token).
    """
    require_admin_token(x_admin_token)

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT public_id, name, created_at FROM games ORDER BY created_at ASC")
        rows = cur.fetchall()
    finally:
        conn.close()

    return [
        GameInfo(
            public_id=row["public_id"],
            name=row["name"],
            created_at=row["created_at"]
        )
        for row in rows
    ]


# ---------- ADMIN: Get game details ----------

@app.get("/games/{public_id}", response_model=GameInfo)
def get_game(public_id: str, x_admin_token: str = Header(None, alias="X-Admin-Token")):
    """
    Admin only: Get game details by public_id (requires X-Admin-Token).
    """
    require_admin_token(x_admin_token)

    conn = get_db()
    try:
        game = get_game_by_public_id(conn, public_id)
    finally:
        conn.close()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return GameInfo(
        public_id=game["public_id"],
        name=game["name"],
        created_at=game["created_at"]
    )


# ---------- OWNER OR ADMIN: Delete highscores ----------

@app.delete("/games/{public_id}/highscores")
def delete_highscores(
    public_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")
):
    """
    Delete all highscores for a game.
    Requires either X-API-Key (game owner) or X-Admin-Token (admin).
    """
    conn = get_db()
    try:
        game = verify_game_ownership_or_admin(conn, public_id, x_api_key, x_admin_token)

        cur = conn.cursor()
        cur.execute("DELETE FROM highscores WHERE game_id = ?", (game["id"],))
        deleted = cur.rowcount
        conn.commit()
    finally:
        conn.close()

    return {"ok": True, "deleted": deleted}


# ---------- OWNER OR ADMIN: Delete game ----------

@app.delete("/games/{public_id}")
def delete_game(
    public_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")
):
    """
    Delete a game and all its highscores.
    Requires either X-API-Key (game owner) or X-Admin-Token (admin).
    """
    conn = get_db()
    try:
        game = verify_game_ownership_or_admin(conn, public_id, x_api_key, x_admin_token)

        cur = conn.cursor()
        cur.execute("DELETE FROM highscores WHERE game_id = ?", (game["id"],))
        cur.execute("DELETE FROM games WHERE id = ?", (game["id"],))
        conn.commit()
    finally:
        conn.close()

    return {"ok": True}
