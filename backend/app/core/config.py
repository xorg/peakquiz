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
    allowed_origins: str = "https://gipfelraten.ch,http://localhost:5173,"
    backend_url: str
    database_url: str = "sqlite:///./peakquiz.db"
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    admin_emails: str = "xorg112@gmail.com"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def admin_emails_list(self) -> list[str]:
        return [e.strip() for e in self.admin_emails.split(",") if e.strip()]

    class Config:
        env_file = _ENV_FILE


settings = Settings()  # type: ignore[call-arg]
