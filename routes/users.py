from fastapi import APIRouter, HTTPException
from typing import List
from models.user import User
from models.conversation import Conversation
from schemas.user import UserCreate, UserResponse, UserLogin, LoginResponse
from schemas.conversation import ConversationResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/signup", response_model=UserResponse)
async def create_user(data: UserCreate):
    """Create a new user"""
    existing_user = await User.find_one(
        {
          "$or": [
          {
            "email": data.email
          }, 
          {
            "username": data.username
          }]
        }
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email or username already exists")
    
    user = User(
        username=data.username,
        email=data.email,
        password_hash=User.hash_password(data.password)
    )
    await user.insert()
    
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
    )

@router.post("/signin", response_model=LoginResponse)
async def login_user(data: UserLogin):
  """Authenticate user and return signin response"""
  user = await User.find_one({"email": data.email})
  
  if not user or not User.verify_password(data.password, user.password_hash):
    raise HTTPException(status_code=401, detail="Invalid email or password")
  
  return LoginResponse(
    id=str(user.id),
    username=user.username,
    email=user.email,
    message="Login successful"
  )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get user by ID"""
    user = await User.get(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email
    )

@router.get("/{user_id}/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(user_id: str):
    """Get all conversations for a user"""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    conversations = await Conversation.find({"user.$id": user.id}).to_list()
    
    return [
        ConversationResponse(
            id=str(conv.id),
            title=conv.title,
            messages=[
                {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
                for msg in conv.messages
            ],
            created_at=conv.created_at,
            updated_at=conv.updated_at
        )
        for conv in conversations
    ]
