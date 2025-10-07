from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv
import os

class Settings(BaseSettings):
    # Database settings
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432

    # Application settings
    SECRET_KEY: str = "change_me"
    APP_PORT: int = 8000
    TZ: str = "Asia/Karachi"
    
    # External service URLs
    ADSPOWER_BASE_URL: str = "http://127.0.0.1:50325"
    BULKCREATE_SERVER_URL: str = "http://127.0.0.1:4000"
    
    # Authentication settings
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    JWT_ALGORITHM: str = "HS256"
    
    # Default admin credentials (for development)
    DEFAULT_ADMIN_EMAIL: str = "admin@example.com"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    
    # CORS settings
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    # Feature flags
    ENABLE_DATABASE_HEALTH_CHECK: bool = True
    ENABLE_AUTO_LOGIN: bool = True
    ENABLE_DEBUG_MODE: bool = False

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
