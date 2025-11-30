from click.decorators import command
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncpg
from .config import settings
from . import database

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.db_pool = await asyncpg.create_pool(
        settings.database_url_pooler,
        min_size=1,
        max_size=10,
        command_timeout=60,
    )
    print("Database pool created")

    # Yield to application
    yield

    # Cleanup on shutdown
    await database.db_pool.close()
    print("Database pool closed")


app = FastAPI(
    title="PickVs API", 
    version="0.1.0", 
    lifespan=lifespan
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
