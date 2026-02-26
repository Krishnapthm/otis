from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_url: str
    num_search_queries: int = 5
    max_retrieved_chunks: int = 20
    use_naive_mcq_generator: bool = False
    chat_graph_retrieval_enabled: bool = True
    chat_router_retrieval_fallback: bool = False

    @property
    def checkpoint_db_url(self) -> str:
        return self.db_url.replace("+asyncpg", "")

    model_config = SettingsConfigDict(
        env_file=".env.fastapi",
        extra="ignore",
    )


settings = Settings()
