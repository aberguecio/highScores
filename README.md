# Highscores API

A lightweight FastAPI-based REST API for managing game leaderboards and highscores.

## Overview

This API allows you to create games and track player highscores with a simple, secure interface. It uses SQLite for storage and provides both public endpoints (for game integration) and admin endpoints (for management).

## Features

- **Public Endpoints**: Create games, submit scores, retrieve leaderboards
- **CORS Enabled**: All origins allowed for easy integration from any domain
- **Owner Authentication**: Each game creator gets a unique API key for managing their game
- **Admin Endpoints**: Full administrative access with admin token
- **SQLite Database**: Lightweight, file-based storage with automatic initialization
- **Email Validation**: Valid email required for game creation
- **Data Validation**: Score limits (0-1B), player name constraints (1-32 chars)
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Traefik Integration**: Automatic HTTPS with Let's Encrypt
- **Persistent Storage**: Data survives container restarts via Docker volumes

## Project Structure

```text
├── app/
│   ├── __init__.py
│   ├── main.py         # FastAPI application and endpoints
│   ├── models.py       # Pydantic models for validation
│   ├── database.py     # Database configuration and helpers
│   └── auth.py         # Authentication functions
├── alembic/            # Database migrations
│   ├── versions/       # Migration scripts
│   └── env.py          # Alembic environment
├── data/               # Database storage (not in git)
├── alembic.ini         # Alembic configuration
├── Dockerfile          # Container image
├── docker-compose.yml  # Docker orchestration
└── requirements.txt    # Python dependencies
```

## API Endpoints

### Public Endpoints (No Authentication)

- `POST /games` - Create a new game (requires email, returns `public_id` and `api_key`)
- `POST /games/{public_id}/highscores` - Submit a highscore
- `GET /games/{public_id}/highscores` - Get top scores (default: 10, max: 50)

### Owner Endpoints (require `X-API-Key` header)

- `DELETE /games/{public_id}/highscores` - Clear all highscores for your game
- `DELETE /games/{public_id}` - Delete your game and all its highscores

### Admin Endpoints (require `X-Admin-Token` header)

- `GET /games` - List all games
- `GET /games/{public_id}` - Get game details
- `DELETE /games/{public_id}/highscores` - Clear all highscores for any game
- `DELETE /games/{public_id}` - Delete any game and all its highscores

## Quick Start

### Local Development (without Docker)

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the application:

```bash
# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

3. Access the API:
   - API: `http://127.0.0.1:8000`
   - Interactive docs: `http://127.0.0.1:8000/docs`

### Docker Deployment (Recommended)

1. Build and start the service:

```bash
docker compose up --build -d
```

2. View logs:

```bash
docker compose logs -f
```

3. Stop the service:

```bash
docker compose down
```

## Security Model

This API implements a dual-authentication system:

### Game Owner Authentication

When you create a game, you receive a unique **API key** (`sk_...`). This key allows you to:

- Delete all highscores for your game
- Delete your entire game

**Important**: Save your API key securely! It's only shown once during game creation and cannot be recovered.

### Admin Authentication

Server administrators can use the `ADMIN_TOKEN` to:

- List and view all games
- Delete any game or highscores
- Full administrative access

## Configuration

### Environment Variables

- `ADMIN_TOKEN` - Authentication token for admin endpoints (default: `"change-me"`)

Create a `.env` file in the project root:

```env
ADMIN_TOKEN=your-secure-token-here
```

## Database Schema

The API automatically creates two tables on startup:

### games

- `id` (INTEGER PRIMARY KEY)
- `public_id` (TEXT UNIQUE) - Public-facing game identifier
- `name` (TEXT) - Game name
- `email` (TEXT) - Creator's email address
- `api_key` (TEXT UNIQUE) - Owner's authentication key
- `created_at` (TEXT) - ISO timestamp

### highscores

- `id` (INTEGER PRIMARY KEY)
- `game_id` (INTEGER FOREIGN KEY)
- `player_name` (TEXT)
- `score` (INTEGER)
- `created_at` (TEXT) - ISO timestamp

## Usage Examples

### Create a Game

```bash
curl -X POST http://localhost:8000/games \
  -H "Content-Type: application/json" \
  -d '{"name": "My Awesome Game", "email": "creator@example.com"}'
```

Response:

```json
{
  "public_id": "g_abc123def456",
  "name": "My Awesome Game",
  "email": "creator@example.com",
  "api_key": "sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "created_at": "2025-11-16T10:30:00.123456"
}
```

**Save the `api_key`! You'll need it to manage your game.**

### Submit a Highscore

```bash
curl -X POST http://localhost:8000/games/g_abc123def456/highscores \
  -H "Content-Type: application/json" \
  -d '{"player_name": "Player1", "score": 9999}'
```

### Get Top Highscores

```bash
# Default: top 10
curl http://localhost:8000/games/g_abc123def456/highscores

# Custom limit (max 50)
curl "http://localhost:8000/games/g_abc123def456/highscores?limit=20"
```

### Delete Highscores (Game Owner)

```bash
curl -X DELETE http://localhost:8000/games/g_abc123def456/highscores \
  -H "X-API-Key: sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Delete Game (Game Owner)

```bash
curl -X DELETE http://localhost:8000/games/g_abc123def456 \
  -H "X-API-Key: sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Admin: List All Games

```bash
curl http://localhost:8000/games \
  -H "X-Admin-Token: your-secure-token-here"
```

### Admin: Delete Any Game

```bash
curl -X DELETE http://localhost:8000/games/g_abc123def456 \
  -H "X-Admin-Token: your-secure-token-here"
```

## Tech Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation and settings management
- **SQLite** - Embedded relational database

## Database Migrations

This project uses Alembic for database schema management. Migrations are automatically run on container startup.

### Creating a New Migration

When you modify the database schema:

```bash
# Create a new migration
alembic revision -m "description of changes"

# Edit the generated file in alembic/versions/
# Add your upgrade() and downgrade() logic

# Apply the migration
alembic upgrade head
```

### Example: Adding a New Column

```python
# alembic/versions/002_add_column.py
def upgrade() -> None:
    op.add_column('games', sa.Column('new_field', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('games', 'new_field')
```

### Migration Commands

```bash
# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

### Important Notes

- **Database persists outside container**: Located in `./data/highscores.db`
- **`docker compose down -v` will NOT delete your database**
- Migrations run automatically on container startup
- For major schema changes, test migrations locally first

## Future Enhancements

- PostgreSQL support for production environments with high concurrency
- Rate limiting for public endpoints
- Score verification/anti-cheat mechanisms
- Pagination for large leaderboards
- WebSocket support for real-time leaderboard updates

## License

This project is open source and available for use in your own projects.
