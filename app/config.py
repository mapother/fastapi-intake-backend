# app/config.py

from pathlib import Path
import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent.parent

if load_dotenv is not None:
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)


class Settings:
    def __init__(self) -> None:
        default_db = f"sqlite:///{(BASE_DIR / 'frederick_fire.db').as_posix()}"
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", default_db)
        self.PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Frederick Fire Chatbot")
        self.API_PREFIX: str = os.getenv("API_PREFIX", "/api")
        
        # Auth settings
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "change_this_in_production_use_openssl_rand_hex_32")
        self.ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        
        # Claude API
        self.ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
        self.CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
        
        # Context settings for chat
        self.MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "20"))


settings = Settings()
