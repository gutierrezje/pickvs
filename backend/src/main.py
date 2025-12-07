from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import database
from .config import settings
from .routers import auth, games


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.db_pool = await asyncpg.create_pool(
        settings.database_url_pooler,
        min_size=1,
        max_size=10,
        command_timeout=60,
    )
    print("Database pool created")

    yield

    await database.db_pool.close()
    print("Database pool closed")


app = FastAPI(title="PickVs API", version="0.1.0", lifespan=lifespan)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(games.router, prefix="/games", tags=["games"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
