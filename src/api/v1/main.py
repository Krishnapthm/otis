from os import getenv
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.routers import auth, embeddings, mcqs, docs, projects, agent, chat
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.agents.graph import graph_builder  # Import the builder


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn_str = "postgresql://user:password@db:5432/otis"

    async with AsyncPostgresSaver.from_conn_string(conn_str) as checkpointer:
        await checkpointer.setup()
        app.state.checkpointer = checkpointer

        # Compile the graph with checkpointer and store it
        app.state.compiled_graph = graph_builder.compile(checkpointer=checkpointer)

        yield


app = FastAPI(
    title="Otis",
    lifespan=lifespan,
    swagger_ui_init_oauth={"usePkceWithAuthorizationCodeGrant": True},
)


app.include_router(mcqs.router, prefix="/v1", tags=["MCQ"])
app.include_router(docs.router, prefix="/v1", tags=["Project Documents"])
app.include_router(docs.user_docs_router, prefix="/v1", tags=["User Documents"])
app.include_router(projects.router, prefix="/v1", tags=["Projects"])
app.include_router(embeddings.router, prefix="/v1", tags=["Embeddings"])
app.include_router(auth.router, prefix="/v1", tags=["Authentication"])
app.include_router(agent.router, prefix="/v1", tags=["Agent"])
app.include_router(chat.router, prefix="/v1", tags=["Chat"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Thread-ID"],
)
