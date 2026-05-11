import cloudinary
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from .api.routes import admin, auth, profile, quiz, rankings
from .core.config import settings
from .db.database import Base, engine

if settings.cloudinary_cloud_name:
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
    )

Base.metadata.create_all(bind=engine)

# Lightweight migrations for additive schema changes
_MIGRATIONS = [
    "ALTER TABLE games ADD COLUMN category TEXT",
    "ALTER TABLE games ADD COLUMN mode TEXT NOT NULL DEFAULT 'timed'",
    "ALTER TABLE pictures ADD COLUMN author_id INTEGER REFERENCES authors(id)",
    "ALTER TABLE pictures ADD COLUMN license_id INTEGER REFERENCES licenses(id)",
    "ALTER TABLE users ADD COLUMN email TEXT",
    "ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0",
]
with engine.connect() as _conn:
    for _sql in _MIGRATIONS:
        try:
            _conn.execute(text(_sql))
            _conn.commit()
        except Exception:
            pass  # Column already exists

app = FastAPI(title="Peakquiz API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(auth.router, prefix="/api")
app.include_router(quiz.router, prefix="/api")
app.include_router(rankings.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
