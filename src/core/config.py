# src/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_url: str

    model_config = SettingsConfigDict(
        env_file=".env.fastapi",
        extra="ignore",
    )


settings = Settings()
