# app/core/config.py
from pydantic_settings import BaseSettings

class Ayarlar(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

ayarlar = Ayarlar()