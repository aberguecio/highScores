"""Pydantic models for request/response validation"""

from pydantic import BaseModel, constr, conint, EmailStr
from typing import List


class GameCreate(BaseModel):
    """Request model for creating a new game"""
    name: constr(min_length=1, max_length=100)
    email: EmailStr


class GameOut(BaseModel):
    """Response model for game creation (includes API key)"""
    public_id: str
    name: str
    email: str
    api_key: str
    created_at: str


class GameInfo(BaseModel):
    """Response model for game information (no sensitive data)"""
    public_id: str
    name: str
    created_at: str


class HighscoreIn(BaseModel):
    """Request model for submitting a highscore"""
    player_name: constr(min_length=1, max_length=32)
    score: conint(ge=0, le=1_000_000_000)


class HighscoreOut(BaseModel):
    """Response model for a single highscore"""
    player_name: str
    score: int
    created_at: str


class HighscoreList(BaseModel):
    """Response model for a list of highscores"""
    game_id: str
    highscores: List[HighscoreOut]
