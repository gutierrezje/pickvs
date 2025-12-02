from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserProfile(BaseModel):
    user_id: UUID
    username: str
    email: EmailStr
    total_units: float
    roi: float
    total_picks: int