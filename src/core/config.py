from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_url: str

    @property
    def checkpoint_db_url(self) -> str:
        return self.db_url.replace("+asyncpg", "")

    model_config = SettingsConfigDict(
        env_file=".env.fastapi",
        extra="ignore",
    )


settings = Settings()
