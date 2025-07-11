import logging
from datetime import datetime
from fastapi import HTTPException
from models.user import User
from models.conversation import Conversation, Message
from agent.financial_agent import analyze_query
from utils.helpers import generate_conversation_title, APIResponse

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for handling financial analysis operations"""
    
    async def analyze(self, query: str, user_id: str, conversation_id: str = None) -> dict:
        """Analyze query and store conversation"""
        try:
            if conversation_id:
                conversation = await Conversation.get(conversation_id)
                if not conversation:
                    raise HTTPException(status_code=404, detail="Conversation not found")
            else:
                user = await User.get(user_id)
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
                
                conversation = Conversation(
                    user=user,
                    title=generate_conversation_title(query)
                )
                await conversation.insert()
            
            user_message = Message(role="user", content=query)
            conversation.messages.append(user_message)
            
            analysis_result = analyze_query(query)
            
            if analysis_result:
                ai_message = Message(role="ai", content=analysis_result)
                conversation.messages.append(ai_message)
                conversation.updated_at = datetime.utcnow()
                await conversation.save()
                
                return {
                    **APIResponse.success(
                        data=analysis_result,
                        message="Analysis completed successfully"
                    ),
                    "conversation_id": str(conversation.id)
                }
            else:
                return APIResponse.error("No analysis result returned")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            return APIResponse.error(f"Analysis failed: {str(e)}")
