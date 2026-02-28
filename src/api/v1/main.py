import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from src.agents.chat_agent import chat_builder
from src.agents.graph import graph_builder
from src.api.crud import mark_stale_messages_failed
from src.api.db.models.session import async_session_maker
from src.api.v1.routers import auth, embeddings, mcqs, docs, projects, agent, chat
from src.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = AsyncConnectionPool(
        conninfo=settings.checkpoint_db_url,
        min_size=1,
        max_size=20,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
    )
    await pool.open()

    checkpointer = AsyncPostgresSaver(conn=pool)
    await checkpointer.setup()

    app.state.pool = pool
    app.state.checkpointer = checkpointer
    app.state.compiled_graph = graph_builder.compile(checkpointer=checkpointer)
    app.state.compiled_chat_graph = chat_builder.compile(checkpointer=checkpointer)

    # ── Startup cleanup: mark stale pending/streaming messages as failed ──
    try:
        async with async_session_maker() as db:
            count = await mark_stale_messages_failed(db)
            if count:
                logger.info(
                    "Startup cleanup: marked %d stale message(s) as failed", count
                )
    except Exception:
        logger.warning(
            "Startup cleanup failed — stale messages may remain", exc_info=True
        )

    try:
        yield
    finally:
        await pool.close()


app = FastAPI(
    title="Otis",
    lifespan=lifespan,
    swagger_ui_init_oauth={"usePkceWithAuthorizationCodeGrant": True},
)


app.include_router(mcqs.router, prefix="/v1", tags=["MCQ"])
app.include_router(mcqs.legacy_router, prefix="/v1", tags=["MCQ"])
app.include_router(docs.router, prefix="/v1", tags=["Project Documents"])
app.include_router(docs.user_docs_router, prefix="/v1", tags=["User Documents"])
app.include_router(projects.router, prefix="/v1", tags=["Projects"])
app.include_router(embeddings.router, prefix="/v1", tags=["Embeddings"])
app.include_router(auth.router, prefix="/v1", tags=["Authentication"])
app.include_router(agent.router, prefix="/v1", tags=["Agent"])
app.include_router(chat.router, prefix="/v1", tags=["Chat"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Thread-ID"],
)
