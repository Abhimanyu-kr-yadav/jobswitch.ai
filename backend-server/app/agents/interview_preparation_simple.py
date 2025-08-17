"""
Simple Interview Preparation Agent for testing
"""
import logging
from typing import Dict, Any, List
from app.agents.base import BaseAgent, AgentResponse, AgentError

logger = logging.getLogger(__name__)


class InterviewPreparationAgent(BaseAgent):
    """Simple interview preparation agent"""
    
    def __init__(self, watsonx_client=None, langchain_manager=None):
        super().__init__("interview_preparation", watsonx_client, langchain_manager)
    
    async def process_request(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process interview preparation requests"""
        return {"success": True, "data": {"message": "Test response"}}
    
    async def get_recommendations(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate interview preparation recommendations"""
        return [{"type": "test", "title": "Test recommendation"}]