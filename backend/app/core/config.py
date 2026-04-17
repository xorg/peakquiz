from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: str
    secret_key: str
    frontend_url: str = "http://localhost:5173"
    database_url: str = "sqlite:///./peakquiz.db"

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore[call-arg]
