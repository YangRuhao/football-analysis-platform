import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.db import check_database, close_pool
from app.routers import compare, leaderboard, players, profile


def _cors_origins():
    raw = os.environ.get("CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501")
    return [item.strip() for item in raw.split(",") if item.strip()]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    check_database()
    try:
        yield
    finally:
        close_pool()


app = FastAPI(
    title="Football Analytics Platform API",
    description="Player stats, comparisons, and leaderboards for Europe's top 5 leagues, 2017/18-2023/24.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["GET"],
    allow_headers=["Accept", "Content-Type"],
    allow_credentials=False,
)

app.include_router(players.router)
app.include_router(compare.router)
app.include_router(leaderboard.router)
app.include_router(profile.router)


@app.get("/health", tags=["health"])
def health_check():
    try:
        check_database()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ok", "database": "ok"}
