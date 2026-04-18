from pathlib import Path
from pydantic_settings import BaseSettings

# Absolute path so the .env is found regardless of working directory (e.g. WSGI servers)
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: str
    secret_key: str
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"
    database_url: str = "sqlite:///./peakquiz.db"

    class Config:
        env_file = _ENV_FILE


settings = Settings()  # type: ignore[call-arg]
