from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class LoginResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    message: str