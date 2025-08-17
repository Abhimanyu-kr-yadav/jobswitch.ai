"""
Working Interview Preparation Agent
"""
from app.agents.base import BaseAgent


class InterviewPreparationAgent(BaseAgent):
    def __init__(self, watsonx_client=None, langchain_manager=None):
        super().__init__("interview_preparation", watsonx_client, langchain_manager)
    
    async def process_request(self, user_input, context):
        return {"success": True, "data": {"message": "Working"}}
    
    async def get_recommendations(self, user_profile):
        return []