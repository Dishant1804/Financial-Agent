from fastapi import APIRouter, HTTPException
from datetime import datetime
from models.user import User
from models.conversation import Conversation
from schemas.conversation import ConversationCreate, ConversationResponse

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.post("", response_model=ConversationResponse)
async def create_conversation(conversation_data: ConversationCreate, user_id: str):
    """Create a new conversation for a user"""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    conversation = Conversation(
        user=user,
        title=conversation_data.title
    )
    await conversation.insert()
    
    return ConversationResponse(
        id=str(conversation.id),
        title=conversation.title,
        messages=[],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Get a specific conversation"""
    conversation = await Conversation.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return ConversationResponse(
        id=str(conversation.id),
        title=conversation.title,
        messages=[
            {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
            for msg in conversation.messages
        ],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )

@router.put("/{conversation_id}")
async def update_conversation(conversation_id: str, update_data: ConversationCreate):
    """Update conversation title"""
    conversation = await Conversation.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if update_data.title:
        conversation.title = update_data.title
    conversation.updated_at = datetime.utcnow()
    await conversation.save()
    
    return {"message": "Conversation updated successfully"}

@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    conversation = await Conversation.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await conversation.delete()
    return {"message": "Conversation deleted successfully"}
