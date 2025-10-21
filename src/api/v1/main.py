from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.routers import mcqs, docs, projects

app = FastAPI(title="Otis")

app.include_router(mcqs.router, prefix="/v1/mcq", tags=["MCQ"])
app.include_router(docs.router, prefix="/v1/projects/documents", tags=["Documents"])
app.include_router(projects.router, prefix="/v1/projects", tags=["Projects"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=[True],
    allow_methods=["*"],
    allow_headers=["*"]
)
