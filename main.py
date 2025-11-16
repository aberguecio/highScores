# main.py
import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Header, Query
from pydantic import BaseModel, constr, conint

DB_PATH = "./highscores.db"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "change-me")  # cámbialo en el server

app = FastAPI(title="Highscores API")


# ========== MODELOS Pydantic ==========

class GameCreate(BaseModel):
    name: constr(min_length=1, max_length=100)


class GameOut(BaseModel):
    public_id: str
    name: str
    created_at: str


class HighscoreIn(BaseModel):
    player_name: constr(min_length=1, max_length=32)
    score: conint(ge=0, le=1_000_000_000)


class HighscoreOut(BaseModel):
    player_name: str
    score: int
    created_at: str


class HighscoreList(BaseModel):
    game_id: str
    highscores: List[HighscoreOut]


# ========== DB HELPERS ==========

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            public_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS highscores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            player_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(game_id) REFERENCES games(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


def get_game_by_public_id(conn, public_id: str) -> Optional[sqlite3.Row]:
    cur = conn.cursor()
    cur.execute("SELECT * FROM games WHERE public_id = ?", (public_id,))
    return cur.fetchone()


# ========== DEPENDENCIA PARA ADMIN ==========

def require_admin_token(x_admin_token: str = Header(None, alias="X-Admin-Token")):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid admin token")


# ========== ENDPOINTS ==========

@app.get("/")
def healthcheck():
    return {"status": "ok"}


# ---------- PÚBLICO: crear juego ----------

@app.post("/games", response_model=GameOut, status_code=201)
def create_game(game: GameCreate):
    """
    Público: cualquiera puede crear un juego nuevo.
    Devuelve public_id, que es el que usarás en el frontend.
    """
    conn = get_db()
    cur = conn.cursor()

    public_id = "g_" + uuid.uuid4().hex[:16]
    now = datetime.utcnow().isoformat()

    try:
        cur.execute(
            "INSERT INTO games (public_id, name, created_at) VALUES (?, ?, ?)",
            (public_id, game.name.strip(), now)
        )
        conn.commit()
    finally:
        conn.close()

    return GameOut(public_id=public_id, name=game.name.strip(), created_at=now)


# ---------- PÚBLICO: enviar highscore ----------

@app.post(
    "/games/{public_id}/highscores",
    response_model=HighscoreOut,
    status_code=201
)
def submit_highscore(public_id: str, hs: HighscoreIn):
    """
    Público: lo usa el juego en JS para guardar un nuevo highscore.
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


# ---------- PÚBLICO: obtener ranking de un juego ----------

@app.get(
    "/games/{public_id}/highscores",
    response_model=HighscoreList
)
def get_highscores(
    public_id: str,
    limit: int = Query(10, ge=1, le=50)
):
    """
    Público: el juego consulta el top N scores.
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


# ---------- ADMIN: listar juegos ----------

@app.get("/games", response_model=List[GameOut])
def list_games(x_admin_token: str = Header(None, alias="X-Admin-Token")):
    """
    Privado: lista todos los juegos (requiere X-Admin-Token).
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
        GameOut(
            public_id=row["public_id"],
            name=row["name"],
            created_at=row["created_at"]
        )
        for row in rows
    ]


# ---------- ADMIN: detalles de un juego ----------

@app.get("/games/{public_id}", response_model=GameOut)
def get_game(public_id: str, x_admin_token: str = Header(None, alias="X-Admin-Token")):
    """
    Privado: detalles de un juego por public_id.
    """
    require_admin_token(x_admin_token)

    conn = get_db()
    try:
        game = get_game_by_public_id(conn, public_id)
    finally:
        conn.close()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return GameOut(
        public_id=game["public_id"],
        name=game["name"],
        created_at=game["created_at"]
    )


# ---------- ADMIN: resetear highscores de un juego ----------

@app.delete("/games/{public_id}/highscores")
def delete_highscores(public_id: str, x_admin_token: str = Header(None, alias="X-Admin-Token")):
    """
    Privado: borra todos los highscores de un juego.
    """
    require_admin_token(x_admin_token)

    conn = get_db()
    try:
        game = get_game_by_public_id(conn, public_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        cur = conn.cursor()
        cur.execute("DELETE FROM highscores WHERE game_id = ?", (game["id"],))
        deleted = cur.rowcount
        conn.commit()
    finally:
        conn.close()

    return {"ok": True, "deleted": deleted}


# ---------- ADMIN: borrar juego completo (opcional) ----------

@app.delete("/games/{public_id}")
def delete_game(public_id: str, x_admin_token: str = Header(None, alias="X-Admin-Token")):
    """
    Privado: borra un juego y todos sus highscores.
    """
    require_admin_token(x_admin_token)

    conn = get_db()
    try:
        game = get_game_by_public_id(conn, public_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        cur = conn.cursor()
        cur.execute("DELETE FROM highscores WHERE game_id = ?", (game["id"],))
        cur.execute("DELETE FROM games WHERE id = ?", (game["id"],))
        conn.commit()
    finally:
        conn.close()

    return {"ok": True}
