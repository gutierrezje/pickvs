from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "AlgoPicker API"
    debug: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
