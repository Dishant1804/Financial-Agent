from beanie import Document, Link
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from models.user import User

class Message(BaseModel):
    role: str = Field(..., description="Either user or ai")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Conversation(Document):
    user: Link[User]
    title: Optional[str] = Field(None, description="Conversation title")
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        collection = "conversations"
