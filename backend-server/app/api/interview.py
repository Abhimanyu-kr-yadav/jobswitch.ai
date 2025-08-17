"""
Interview Preparation API endpoints
"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from pydantic import BaseModel, Field
import os
import uuid

from app.core.auth import get_current_user
from app.agents.interview_preparation import InterviewPreparationAgent
from app.integrations.watsonx import WatsonXClient
# LangChain manager is available in app.state.langchain_manager
from app.models.interview import (
    GenerateQuestionsRequest, StartMockInterviewRequest, SubmitResponseRequest,
    EndSessionRequest, GetFeedbackRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents/interview-preparation", tags=["interview"])


# Additional request models for backward compatibility
class LegacyStartMockInterviewRequest(BaseModel):
    job_role: str = Field(..., description="Target job role")
    company: str = Field("", description="Target company (optional)")
    question_count: int = Field(5, ge=3, le=10, description="Number of questions for interview")
    categories: List[str] = Field(["behavioral", "technical"], description="Question categories")
    recording_mode: str = Field("audio", description="Recording mode: audio or video")


# Dependency to get interview agent
async def get_interview_agent(request: Request) -> InterviewPreparationAgent:
    """Get interview preparation agent instance"""
    try:
        watsonx_client = request.app.state.watsonx_client
        langchain_manager = request.app.state.langchain_manager
        return InterviewPreparationAgent(watsonx_client, langchain_manager)
    except Exception as e:
        logger.error(f"Failed to initialize interview agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initialize interview service")


@router.post("/generate-questions")
async def generate_questions(
    request: GenerateQuestionsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: InterviewPreparationAgent = Depends(get_interview_agent)
):
    """
    Generate interview questions based on job role, company, and skills
    """
    try:
        user_input = {
            "action": "generate_questions",
            "job_role": request.job_role,
            "company": request.company,
            "skills": request.skills,
            "question_count": request.question_count,
            "categories": request.categories
        }
        
        context = {"user_id": current_user["user_id"]}
        
        result = await agent.process_request(user_input, context)
        
        if result.get("success"):
            return {
                "success": True,
                "data": result["data"]
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Question generation failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/start-mock-interview")
async def start_mock_interview(
    request: StartMockInterviewRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: InterviewPreparationAgent = Depends(get_interview_agent)
):
    """
    Start a new mock interview session
    """
    try:
        user_input = {
            "action": "start_mock_interview",
            "job_role": request.job_role,
            "company": request.company,
            "question_count": request.question_count,
            "categories": request.categories
        }
        
        context = {"user_id": current_user["user_id"]}
        
        result = await agent.process_request(user_input, context)
        
        if result.get("success"):
            return {
                "success": True,
                "data": result["data"]
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to start mock interview"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mock interview start error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/submit-response")
async def submit_response(
    request: SubmitResponseRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: InterviewPreparationAgent = Depends(get_interview_agent)
):
    """
    Submit response to interview question
    """
    try:
        user_input = {
            "action": "submit_response",
            "session_id": request.session_id,
            "response": request.response,
            "response_time": request.response_time
        }
        
        context = {"user_id": current_user["user_id"]}
        
        result = await agent.process_request(user_input, context)
        
        if result.get("success"):
            return {
                "success": True,
                "data": result["data"]
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to submit response"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Response submission error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/end-session")
async def end_session(
    request: EndSessionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: InterviewPreparationAgent = Depends(get_interview_agent)
):
    """
    End an active interview session
    """
    try:
        user_input = {
            "action": "end_session",
            "session_id": request.session_id
        }
        
        context = {"user_id": current_user["user_id"]}
        
        result = await agent.process_request(user_input, context)
        
        if result.get("success"):
            return {
                "success": True,
                "data": result["data"]
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to end session"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session end error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/get-feedback")
async def get_feedback(
    request: GetFeedbackRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: InterviewPreparationAgent = Depends(get_interview_agent)
):
    """
    Get feedback for completed interview session
    """
    try:
        user_input = {
            "action": "get_feedback",
            "session_id": request.session_id
        }
        
        context = {"user_id": current_user["user_id"]}
        
        result = await agent.process_request(user_input, context)
        
        if result.get("success"):
            return {
                "success": True,
                "data": result["data"]
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to generate feedback"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/recommendations")
async def get_recommendations(
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: InterviewPreparationAgent = Depends(get_interview_agent)
):
    """
    Get interview preparation recommendations for the user
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
                {"name": "Python", "proficiency": 2},
                {"name": "System Design", "proficiency": 2}
            ],
            "recent_applications": [
                {"company": "Google", "role": "Software Engineer"},
                {"company": "Microsoft", "role": "Full Stack Developer"}
            ]
        }
        
        recommendations = await agent.get_recommendations(user_profile)
        
        return {
            "success": True,
            "data": {
                "recommendations": recommendations,
                "user_id": current_user["user_id"]
            }
        }
        
    except Exception as e:
        logger.error(f"Recommendations error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/upload-recording")
async def upload_recording(
    session_id: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload audio or video recording for interview response
    """
    try:
        # Validate file type
        allowed_types = {
            'audio/webm', 'audio/wav', 'audio/mp3', 'audio/ogg',
            'video/webm', 'video/mp4', 'video/quicktime'
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'webm'
        unique_filename = f"{session_id}_{uuid.uuid4()}.{file_extension}"
        
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/recordings"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Return file URL (in production, this would be a proper URL)
        file_url = f"/uploads/recordings/{unique_filename}"
        
        return {
            "success": True,
            "data": {
                "file_url": file_url,
                "file_type": file.content_type,
                "file_size": len(content)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="File upload failed")


@router.post("/process-speech-to-text")
async def process_speech_to_text(
    request: dict,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: InterviewPreparationAgent = Depends(get_interview_agent)
):
    """
    Process audio file to extract text using speech-to-text with enhanced analysis
    """
    try:
        audio_url = request.get("audio_url")
        if not audio_url:
            raise HTTPException(status_code=400, detail="Audio URL is required")
        
        # Process speech-to-text with enhanced analysis
        transcript = await agent._process_speech_to_text(audio_url)
        
        if transcript:
            return {
                "success": True,
                "data": {
                    "transcript": transcript,
                    "audio_url": audio_url,
                    "analysis": {
                        "word_count": transcript.get("word_count", 0),
                        "speaking_rate": transcript.get("speaking_rate", 0),
                        "clarity_score": transcript.get("clarity_score", 0),
                        "filler_words": transcript.get("filler_words", []),
                        "confidence": transcript.get("confidence", 0),
                        "duration": transcript.get("audio_duration", 0)
                    }
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to process audio")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Speech-to-text processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Speech processing failed")


@router.post("/analyze-speech-patterns")
async def analyze_speech_patterns(
    request: dict,
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent: InterviewPreparationAgent = Depends(get_interview_agent)
):
    """
    Analyze speech patterns from multiple audio responses
    """
    try:
        audio_urls = request.get("audio_urls", [])
        if not audio_urls:
            raise HTTPException(status_code=400, detail="Audio URLs are required")
        
        # Process each audio file
        speech_analyses = []
        for audio_url in audio_urls:
            transcript = await agent._process_speech_to_text(audio_url)
            if transcript:
                speech_analyses.append(transcript)
        
        if not speech_analyses:
            raise HTTPException(status_code=400, detail="No audio files could be processed")
        
        # Calculate overall speech patterns
        avg_speaking_rate = sum(s.get("speaking_rate", 150) for s in speech_analyses) / len(speech_analyses)
        avg_clarity = sum(s.get("clarity_score", 0.8) for s in speech_analyses) / len(speech_analyses)
        total_filler_words = sum(len(s.get("filler_words", [])) for s in speech_analyses)
        
        overall_analysis = {
            "total_responses": len(speech_analyses),
            "average_speaking_rate": avg_speaking_rate,
            "average_clarity_score": avg_clarity,
            "total_filler_words": total_filler_words,
            "speech_quality_score": (avg_clarity * 0.6 + min(1.0, 150/avg_speaking_rate) * 0.4) * 100,
            "individual_analyses": speech_analyses
        }
        
        return {
            "success": True,
            "data": overall_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Speech pattern analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Speech analysis failed")