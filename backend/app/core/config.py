from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv
import os

class Settings(BaseSettings):
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432

    SECRET_KEY: str = "change_me"
    APP_PORT: int = 8000
    ADSPOWER_BASE_URL: str = "http://127.0.0.1:50325"
    TZ: str = "Asia/Karachi"

    class Config:
        env_file = ".env"
        extra = "ignore"   # <-- allow extra envs if present


# Ensure the backend/.env is loaded regardless of current working directory
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=_env_path, override=False)

# Normalize potential BOM-prefixed keys (UTF-8 BOM on Windows editors)
def _normalize_bom(key: str) -> None:
    bom_key = "\ufeff" + key
    if bom_key in os.environ and key not in os.environ:
        os.environ[key] = os.environ[bom_key]

for __k in (
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "SECRET_KEY",
    "APP_PORT",
    "ADSPOWER_BASE_URL",
    "TZ",
):
    _normalize_bom(__k)

settings = Settings()
