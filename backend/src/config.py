from os import access
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url_pooler: str
    #secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    app_name: str = "AlgoPicker API"
    debug: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
