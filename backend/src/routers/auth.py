from datetime import timedelta
from typing import Annotated

from asyncpg import Connection
from fastapi import APIRouter, Depends, HTTPException, status

from database import get_db
from models.user import TokenResponse, UserLogin, UserRegister
from utils.auth import create_access_token, hash_password, verify_password

router = APIRouter()

ConnectionDep = Annotated[Connection, Depends(get_db)]


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister, conn: ConnectionDep):
    """Register a new user."""
    # Check if username already exists
    existing_user = await conn.fetchrow(
        "SELECT user_id FROM Users WHERE username = $1", user.username
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already exists"
        )

    existing_email = await conn.fetchrow(
        "SELECT user_id FROM Users WHERE email = $1", user.email
    )
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    # Hash password and insert new user
    pwd_hash = hash_password(user.password)
    user_id = await conn.fetchval(
        """
        INSERT INTO Users (username, email, password_hash)
        VALUES ($1, $2, $3)
        RETURNING user_id
        """,
        user.username,
        user.email,
        pwd_hash,
    )

    return {"user_id": user_id, "message": "User registered successfully"}


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, conn: ConnectionDep):
    """Authenticate user and return JWT token."""
    # Fetch user from database
    user = await conn.fetchrow(
        "SELECT user_id, password_hash FROM Users WHERE username = $1",
        credentials.username,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": str(user["user_id"])}, expires_delta=access_token_expires
    )

    return TokenResponse(access_token=access_token, token_type="bearer")
