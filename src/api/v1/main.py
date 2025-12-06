from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.routers import auth, embeddings, mcqs, docs, projects

app = FastAPI(title="Otis", swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    }
)


app.include_router(mcqs.router, prefix="/v1", tags=["MCQ"])
app.include_router(docs.router, prefix="/v1", tags=["Documents"])
app.include_router(projects.router, prefix="/v1", tags=["Projects"])
app.include_router(embeddings.router, prefix="/v1", tags=["Embeddings"])
app.include_router(auth.router, prefix="/v1", tags=["Authentication"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
