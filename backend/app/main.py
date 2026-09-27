from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
 
from app.routers import compare, leaderboard, players

app = FastAPI(
    title="Football Analytics Platform API",
    description=("Player stats, comparisons, and leaderboards for Europe's top 5 " 
                 "leagues, 2017/18-2023/24."
                ),
    version="0.1.0",
    )
   
# The Streamlit dashboard runs on a different port during local dev.
# Tighten allow_origins to the dashboard's actual deployed URL before
# putting this anywhere public.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(players.router)
app.include_router(compare.router)
app.include_router(leaderboard.router)
   
@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
