"""Shared FastAPI dependencies."""

from typing import Annotated

from asyncpg import Connection
from fastapi import Depends

from database import get_db
from utils.auth import get_current_user

# Database connection dependency
ConnectionDep = Annotated[Connection, Depends(get_db)]

# Authenticated user dependency (returns user_id)
CurrentUserDep = Annotated[str, Depends(get_current_user)]
