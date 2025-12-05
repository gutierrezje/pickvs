import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import database
from .config import settings
from .routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Use TEST_DATABASE_URL if available (for tests), otherwise use production URL
    db_url = settings.database_url_pooler

    database.db_pool = await asyncpg.create_pool(
        db_url,
        min_size=1,
        max_size=10,
        command_timeout=60,
    )
    print(
        f"Database pool created ({'TEST' if os.getenv('TEST_DATABASE_URL') else 'PROD'})"
    )

    # Yield to application
    yield

    # Cleanup on shutdown
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


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
