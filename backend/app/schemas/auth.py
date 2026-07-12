from pydantic import BaseModel, EmailStr
import uuid

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserCreateRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str  # must be one of: fleet_manager, dispatcher, safety_officer, financial_analyst

class UserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True
