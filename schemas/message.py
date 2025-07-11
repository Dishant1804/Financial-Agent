from pydantic import BaseModel, Field
from datetime import datetime

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)

class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: datetime