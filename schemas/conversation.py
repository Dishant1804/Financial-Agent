from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from schemas.message import MessageResponse

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    id: str
    title: Optional[str]
    messages: List[MessageResponse]
    created_at: datetime
    updated_at: datetime