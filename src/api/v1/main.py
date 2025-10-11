from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers import mcqs

app = FastAPI(title="Otis")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=[True],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(mcqs.router)

@app.get("/")

async def root():
    return {"hello":"world"}