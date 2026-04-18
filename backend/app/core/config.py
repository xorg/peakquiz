from pathlib import Path
from pydantic_settings import BaseSettings

# Absolute path so the .env is found regardless of working directory (e.g. WSGI servers)
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: str
    secret_key: str
    # Comma-separated list of allowed frontend origins, e.g.:
    # ALLOWED_ORIGINS=https://gipfelraten.stefanschneider.me,https://xorg.github.io
    allowed_origins: str = "https://gipfelraten.stefanschneider.me,http://localhost:5173,"
    backend_url: str = "peakquiz-backend-295049646559.europe-west1.run.app"
    database_url: str = "sqlite:///./peakquiz.db"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    class Config:
        env_file = _ENV_FILE


settings = Settings()  # type: ignore[call-arg]
