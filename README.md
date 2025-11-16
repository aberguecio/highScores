# highscores

Pequeña API en FastAPI para guardar highscores de juegos.

Qué incluye esta carpeta:

- `main.py` - la API principal (usa SQLite por defecto, archivo `highscores.db`).
- `Dockerfile` - para construir la imagen de la app.
- `docker-compose.yml` - para correr la app y persistir la base (SQLite) en un volumen.
- `requirements.txt` - dependencias Python.

Cómo funciona la base de datos (rápido):
- `main.py` llama a `init_db()` al arrancar: crea `games` y `highscores` si no existen.
- El archivo SQLite resultante se llama `highscores.db` y se crea en el directorio de trabajo.

Ejecutar localmente (sin Docker):

1. Crear un entorno virtual e instalar dependencias:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

2. Ejecutar la app:

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

3. La API estará en `http://127.0.0.1:8000`. La documentación interactiva en `/docs`.

Usar Docker Compose (recomendado para despliegue simple):

1. Construir y levantar:

```powershell
docker compose up --build -d
```

2. Ver logs:

```powershell
docker compose logs -f
```

3. Parar y eliminar:

```powershell
docker compose down
```

Notas sobre persistencia y alternativas:

- La configuración de `docker-compose.yml` guarda todo el directorio de la app en un volumen Docker,
  por lo tanto `highscores.db` persistirá entre reinicios.
- Si prefieres usar PostgreSQL (más apropiado para producción concurrente), puedo darte una versión
  alternativa del `docker-compose.yml` y los cambios mínimos necesarios en `main.py` para usar
  PostgreSQL con `psycopg2` o migrar a SQLAlchemy.

Si quieres, implemento también la versión con PostgreSQL y la adaptación del código.