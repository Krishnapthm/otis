from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    num_search_queries: int = 5
    max_retrieved_chunks: int = 20
    use_naive_mcq_generator: bool = False
    chat_graph_retrieval_enabled: bool = True
    chat_router_retrieval_fallback: bool = False

    # Token chunk buffering for event persistence
    token_chunk_size: int = 50  # Flush after accumulating this many chars
    token_chunk_flush_ms: int = 200  # Flush after this many ms since last flush

    @property
    def checkpoint_db_url(self) -> str:
        return self.db_url.replace("+asyncpg", "")

    model_config = SettingsConfigDict(
        env_file=".env.fastapi",
        extra="ignore",
    )


settings = Settings()
