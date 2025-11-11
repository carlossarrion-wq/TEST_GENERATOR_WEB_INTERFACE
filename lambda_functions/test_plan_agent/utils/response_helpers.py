"""
Response helper functions for LangChain agent
"""

from typing import Dict, Any

def create_success_response(data: Dict[str, Any], execution_id: str = None) -> Dict[str, Any]:
    """Create successful response"""
    response = {
        "success": True,
        "data": data
    }
    if execution_id:
        response["execution_id"] = execution_id
    return response

def create_error_response(message: str, execution_id: str = None) -> Dict[str, Any]:
    """Create error response"""
    response = {
        "success": False,
        "error": message
    }
    if execution_id:
        response["execution_id"] = execution_id
    return response
