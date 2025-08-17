"""
Technical Interview API endpoints
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request

from app.core.auth import get_current_user
from app.agents.technical_interview import TechnicalInterviewAgent
from app.integrations.watsonx import WatsonXClient
# LangChain manager is available in app.state.langchain_manager
from app.models.coding_challenge import (
    GetChallengesRequest, StartTechnicalInterviewRequest, SubmitCodeRequest,
    ExecuteCodeRequest, GetTechnicalFeedbackRequest, ChallengesResponse,
    TechnicalInterviewResponse, CodeExecutionResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents/technical-interview", tags=["technical-interview"])


# Dependency to get technical interview agent
async def get_technical_interview_agent(request: Request) -> TechnicalInterviewAgent:
    """Get technical interview agent instance"""
    try:
        watsonx_client = request.app.state.watsonx_client
        langchain_manager = request.app.state.langchain_manager
        return TechnicalInterviewAgent(watsonx_client, langchain_manager)
    except Exception as e:
        logger.error(f"Failed to initialize technical interview agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initialize technical interview service")


@router.get("/challenges")
async def get_challenges(
    difficulty: str = None,
    category: str = None,
    company: str = None,
    limit: int = 20,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: TechnicalInterviewAgent = Depends(get_technical_interview_agent)
):
    """
    Get coding challenges with optional filtering
    """
    try:
        user_input = {
            "action": "get_challenges",
            "difficulty": difficulty,
            "category": category,
            "company": company,
            "limit": limit,
            "offset": offset
        }
        
        context = {"user_id": current_user["user_id"]}
        
        result = await agent.process_request(user_input, context)
        
        if result.get("success"):
            return ChallengesResponse(
                success=True,
                data=result["data"]
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get challenges"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get challenges error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/start-interview")
async def start_technical_interview(
    request: StartTechnicalInterviewRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: TechnicalInterviewAgent = Depends(get_technical_interview_agent)
):
    """
    Start a new technical interview session
    """
    try:
        user_input = {
            "action": "start_technical_interview",
            "job_role": request.job_role,
            "company": request.company,
            "difficulty": request.difficulty,
            "categories": request.categories,
            "challenge_count": request.challenge_count,
            "time_limit": request.time_limit
        }
        
        context = {"user_id": current_user["user_id"]}
        
        result = await agent.process_request(user_input, context)
        
        if result.get("success"):
            return TechnicalInterviewResponse(
                success=True,
                data=result["data"]
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to start technical interview"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start technical interview error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/current-challenge")
async def get_current_challenge(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: TechnicalInterviewAgent = Depends(get_technical_interview_agent)
):
    """
    Get the current challenge for an active session
    """
    try:
        user_input = {
            "action": "get_current_challenge",
            "session_id": session_id
        }
        
        context = {"user_id": current_user["user_id"]}
        
        result = await agent.process_request(user_input, context)
        
        if result.get("success"):
            return TechnicalInterviewResponse(
                success=True,
                data=result["data"]
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get current challenge"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current challenge error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/submit-code")
async def submit_code(
    request: SubmitCodeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: TechnicalInterviewAgent = Depends(get_technical_interview_agent)
):
    """
    Submit code solution for evaluation
    """
    try:
        user_input = {
            "action": "submit_code",
            "session_id": request.session_id,
            "challenge_id": request.challenge_id,
            "language": request.language,
            "code": request.code
        }
        
        context = {"user_id": current_user["user_id"]}
        
        result = await agent.process_request(user_input, context)
        
        if result.get("success"):
            return TechnicalInterviewResponse(
                success=True,
                data=result["data"]
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to submit code"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit code error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/execute-code")
async def execute_code(
    request: ExecuteCodeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: TechnicalInterviewAgent = Depends(get_technical_interview_agent)
):
    """
    Execute code without submitting (for testing)
    """
    try:
        user_input = {
            "action": "execute_code",
            "challenge_id": request.challenge_id,
            "language": request.language,
            "code": request.code,
            "test_cases": request.test_cases
        }
        
        context = {"user_id": current_user["user_id"]}
        
        result = await agent.process_request(user_input, context)
        
        if result.get("success"):
            return CodeExecutionResponse(
                success=True,
                data=result["data"]
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to execute code"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execute code error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/hint")
async def get_hint(
    session_id: str,
    hint_level: int = 1,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: TechnicalInterviewAgent = Depends(get_technical_interview_agent)
):
    """
    Get hint for current challenge
    """
    try:
        user_input = {
            "action": "get_hint",
            "session_id": session_id,
            "hint_level": hint_level
        }
        
        context = {"user_id": current_user["user_id"]}
        
        result = await agent.process_request(user_input, context)
        
        if result.get("success"):
            return TechnicalInterviewResponse(
                success=True,
                data=result["data"]
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get hint"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get hint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/skip-challenge")
async def skip_challenge(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: TechnicalInterviewAgent = Depends(get_technical_interview_agent)
):
    """
    Skip current challenge and move to next
    """
    try:
        user_input = {
            "action": "skip_challenge",
            "session_id": session_id
        }
        
        context = {"user_id": current_user["user_id"]}
        
        result = await agent.process_request(user_input, context)
        
        if result.get("success"):
            return TechnicalInterviewResponse(
                success=True,
                data=result["data"]
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to skip challenge"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Skip challenge error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/end-interview")
async def end_technical_interview(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: TechnicalInterviewAgent = Depends(get_technical_interview_agent)
):
    """
    End technical interview session
    """
    try:
        user_input = {
            "action": "end_technical_interview",
            "session_id": session_id
        }
        
        context = {"user_id": current_user["user_id"]}
        
        result = await agent.process_request(user_input, context)
        
        if result.get("success"):
            return TechnicalInterviewResponse(
                success=True,
                data=result["data"]
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to end interview"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"End technical interview error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/feedback")
async def get_technical_feedback(
    request: GetTechnicalFeedbackRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: TechnicalInterviewAgent = Depends(get_technical_interview_agent)
):
    """
    Get comprehensive technical interview feedback
    """
    try:
        user_input = {
            "action": "get_technical_feedback",
            "session_id": request.session_id
        }
        
        context = {"user_id": current_user["user_id"]}
        
        result = await agent.process_request(user_input, context)
        
        if result.get("success"):
            return TechnicalInterviewResponse(
                success=True,
                data=result["data"]
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to generate feedback"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get technical feedback error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/recommendations")
async def get_recommendations(
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: TechnicalInterviewAgent = Depends(get_technical_interview_agent)
):
    """
    Get technical interview preparation recommendations for the user
    """
    try:
        # Get user profile (this would typically come from a user service)
        user_profile = {
            "user_id": current_user["user_id"],
            "career_goals": {
                "target_roles": ["Software Engineer", "Full Stack Developer"]
            },
            "skills": [
                {"name": "JavaScript", "proficiency": 4},
                {"name": "Python", "proficiency": 3},
                {"name": "Data Structures", "proficiency": 2},
                {"name": "Algorithms", "proficiency": 2}
            ]
        }
        
        recommendations = await agent.get_recommendations(user_profile)
        
        return TechnicalInterviewResponse(
            success=True,
            data={
                "recommendations": recommendations,
                "user_id": current_user["user_id"]
            }
        )
        
    except Exception as e:
        logger.error(f"Recommendations error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/challenge/{challenge_id}")
async def get_challenge_details(
    challenge_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get details for a specific challenge
    """
    try:
        from app.data.coding_challenges import get_challenge_by_id
        
        challenge = get_challenge_by_id(challenge_id)
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Remove solution from response for security
        challenge_data = challenge.dict()
        challenge_data.pop("solution", None)
        
        return ChallengesResponse(
            success=True,
            data={"challenge": challenge_data}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get challenge details error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/categories")
async def get_challenge_categories(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get available challenge categories
    """
    try:
        from app.models.coding_challenge import CodingCategory, CodingDifficulty
        
        categories = [category.value for category in CodingCategory]
        difficulties = [difficulty.value for difficulty in CodingDifficulty]
        
        return ChallengesResponse(
            success=True,
            data={
                "categories": categories,
                "difficulties": difficulties
            }
        )
        
    except Exception as e:
        logger.error(f"Get categories error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")