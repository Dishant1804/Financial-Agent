from datetime import datetime
from typing import Optional

def generate_conversation_title(query: str, max_length: int = 50) -> str:
    """Generate a conversation title from a query"""
    if len(query) <= max_length:
        return query
    return query[:max_length] + "..."

def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """Format timestamp for API responses"""
    if timestamp is None:
        timestamp = datetime.utcnow()
    return timestamp.isoformat() + "Z"

def validate_object_id(object_id: str) -> bool:
    """Validate MongoDB ObjectId format"""
    import re
    return bool(re.match(r'^[0-9a-fA-F]{24}$', object_id))

class APIResponse:
    """Standardized API response helper"""
    
    @staticmethod
    def success(data=None, message="Success"):
        return {
            "status": "success",
            "message": message,
            "data": data
        }
    
    @staticmethod
    def error(message="Error occurred", error_code=None):
        response = {
            "status": "error",
            "message": message
        }
        if error_code:
            response["error_code"] = error_code
        return response
    
    @staticmethod
    def not_found(resource="Resource"):
        return {
            "status": "error",
            "message": f"{resource} not found",
            "error_code": "NOT_FOUND"
        }
