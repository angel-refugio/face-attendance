from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    FLASK_ENV: str = Field(default="development", alias="FLASK_ENV")
    DEBUG: bool = Field(default=True, alias="FLASK_DEBUG")
    HOST: str = Field(default="0.0.0.0", alias="FLASK_HOST")
    PORT: int = Field(default=5000, alias="FLASK_PORT")
    SECRET_KEY: str = Field(default="dev-secret-key-change-me", alias="SECRET_KEY")

    DATABASE_URL: str = Field(
        default=f"sqlite:///{BASE_DIR / 'app.db'}",
        alias="DATABASE_URL",
    )

    ADMIN_USERNAME: str = Field(default="admin", alias="ADMIN_USERNAME")
    ADMIN_PASSWORD: str = Field(default="admin123", alias="ADMIN_PASSWORD")

    FACES_DIR: str = Field(
        default=str(BASE_DIR / "app" / "static" / "uploads" / "rostros"),
        alias="FACES_DIR",
    )

    CONFIDENCE_THRESHOLD: float = Field(default=70.0, alias="CONFIDENCE_THRESHOLD")
    DUPLICATE_WINDOW_MINUTES: int = Field(default=5, alias="DUPLICATE_WINDOW_MINUTES")

    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
