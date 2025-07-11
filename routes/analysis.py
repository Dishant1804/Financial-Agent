from fastapi import APIRouter
import logging
from schemas.analysis import AnalysisRequest
from services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["analysis"])

@router.post("/analyze")
async def analyze_financial_query(request: AnalysisRequest):
    """Analyze financial query and store conversation"""
    logger.info(f"Received analysis request from user {request.user_id}: {request.query[:100]}...")
    
    analysis_service = AnalysisService()
    result = await analysis_service.analyze(request.query, request.user_id, request.conversation_id)
    return result
