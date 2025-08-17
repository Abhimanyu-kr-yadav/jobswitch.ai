"""
Interview data models and schemas
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class InterviewQuestionCategory(str, Enum):
    """Interview question categories"""
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    COMPANY = "company"
    GENERAL = "general"


class InterviewQuestionDifficulty(str, Enum):
    """Interview question difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class InterviewSessionStatus(str, Enum):
    """Interview session status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ENDED = "ended"
    EXPIRED = "expired"


class InterviewQuestion(BaseModel):
    """Interview question model"""
    id: str = Field(..., description="Unique question identifier")
    question: str = Field(..., description="The interview question text")
    category: InterviewQuestionCategory = Field(..., description="Question category")
    difficulty: InterviewQuestionDifficulty = Field(..., description="Question difficulty")
    time_limit: int = Field(120, description="Suggested time limit in seconds")
    key_points: List[str] = Field(default_factory=list, description="Key points to address")
    answer_structure: Optional[str] = Field(None, description="Suggested answer structure")
    
    class Config:
        use_enum_values = True


class InterviewResponse(BaseModel):
    """Interview response model"""
    question_id: str = Field(..., description="ID of the question being answered")
    response: str = Field(..., description="User's text response")
    response_time: int = Field(..., description="Time taken to respond in seconds")
    audio_url: Optional[str] = Field(None, description="URL to audio recording")
    video_url: Optional[str] = Field(None, description="URL to video recording")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InterviewSession(BaseModel):
    """Interview session model"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier")
    job_role: str = Field(..., description="Target job role")
    company: Optional[str] = Field(None, description="Target company")
    questions: List[InterviewQuestion] = Field(..., description="Interview questions")
    responses: List[InterviewResponse] = Field(default_factory=list, description="User responses")
    current_question_index: int = Field(0, description="Current question index")
    status: InterviewSessionStatus = Field(InterviewSessionStatus.ACTIVE, description="Session status")
    recording_mode: str = Field("audio", description="Recording mode: audio or video")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Session start time")
    completed_at: Optional[datetime] = Field(None, description="Session completion time")
    ended_at: Optional[datetime] = Field(None, description="Session end time")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InterviewFeedbackItem(BaseModel):
    """Individual question feedback"""
    question_index: int = Field(..., description="Question index in the session")
    question_id: str = Field(..., description="Question identifier")
    score: int = Field(..., ge=0, le=100, description="Score for this question")
    feedback: str = Field(..., description="Detailed feedback for the response")
    strengths: List[str] = Field(default_factory=list, description="Response strengths")
    improvements: List[str] = Field(default_factory=list, description="Areas for improvement")


class InterviewFeedback(BaseModel):
    """Complete interview feedback"""
    session_id: str = Field(..., description="Interview session identifier")
    overall_score: int = Field(..., ge=0, le=100, description="Overall interview score")
    strengths: List[str] = Field(default_factory=list, description="Overall strengths")
    areas_for_improvement: List[str] = Field(default_factory=list, description="Areas for improvement")
    detailed_feedback: List[InterviewFeedbackItem] = Field(default_factory=list, description="Question-by-question feedback")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Feedback generation time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InterviewPreparationRecommendation(BaseModel):
    """Interview preparation recommendation"""
    type: str = Field(..., description="Recommendation type")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Recommendation description")
    priority: str = Field("medium", description="Priority level: low, medium, high")
    estimated_time: str = Field(..., description="Estimated time to complete")
    action: Dict[str, Any] = Field(..., description="Action parameters")


# Request/Response schemas for API endpoints
class GenerateQuestionsRequest(BaseModel):
    """Request schema for generating interview questions"""
    job_role: str = Field(..., description="Target job role")
    company: str = Field("", description="Target company (optional)")
    skills: List[str] = Field(default_factory=list, description="Relevant skills")
    question_count: int = Field(10, ge=1, le=20, description="Number of questions to generate")
    categories: List[InterviewQuestionCategory] = Field(
        [InterviewQuestionCategory.BEHAVIORAL, InterviewQuestionCategory.TECHNICAL],
        description="Question categories"
    )


class StartMockInterviewRequest(BaseModel):
    """Request schema for starting a mock interview"""
    job_role: str = Field(..., description="Target job role")
    company: str = Field("", description="Target company (optional)")
    question_count: int = Field(5, ge=3, le=10, description="Number of questions for interview")
    categories: List[InterviewQuestionCategory] = Field(
        [InterviewQuestionCategory.BEHAVIORAL, InterviewQuestionCategory.TECHNICAL],
        description="Question categories"
    )
    recording_mode: str = Field("audio", description="Recording mode: audio or video")


class SubmitResponseRequest(BaseModel):
    """Request schema for submitting interview response"""
    session_id: str = Field(..., description="Interview session ID")
    response: str = Field(..., description="User's response to the question")
    response_time: int = Field(..., ge=0, description="Time taken to respond in seconds")
    audio_url: Optional[str] = Field(None, description="URL to audio recording")
    video_url: Optional[str] = Field(None, description="URL to video recording")


class EndSessionRequest(BaseModel):
    """Request schema for ending interview session"""
    session_id: str = Field(..., description="Interview session ID")


class GetFeedbackRequest(BaseModel):
    """Request schema for getting interview feedback"""
    session_id: str = Field(..., description="Interview session ID")


# Response schemas
class GenerateQuestionsResponse(BaseModel):
    """Response schema for question generation"""
    success: bool = Field(..., description="Success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")


class MockInterviewResponse(BaseModel):
    """Response schema for mock interview operations"""
    success: bool = Field(..., description="Success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")


class InterviewRecommendationsResponse(BaseModel):
    """Response schema for interview recommendations"""
    success: bool = Field(..., description="Success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data containing recommendations")
    error: Optional[str] = Field(None, description="Error message if failed")