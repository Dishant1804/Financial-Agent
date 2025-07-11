from pydantic import BaseModel, Field
from typing import Optional

class AnalysisRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Financial analysis query")
    user_id: str = Field(..., description="User ID")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")