"""
Coding Challenge data models and schemas for technical interviews
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CodingDifficulty(str, Enum):
    """Coding challenge difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class CodingCategory(str, Enum):
    """Coding challenge categories"""
    ARRAYS = "arrays"
    STRINGS = "strings"
    LINKED_LISTS = "linked_lists"
    TREES = "trees"
    GRAPHS = "graphs"
    DYNAMIC_PROGRAMMING = "dynamic_programming"
    SORTING = "sorting"
    SEARCHING = "searching"
    HASH_TABLES = "hash_tables"
    STACKS_QUEUES = "stacks_queues"
    RECURSION = "recursion"
    GREEDY = "greedy"
    BACKTRACKING = "backtracking"
    SYSTEM_DESIGN = "system_design"


class ProgrammingLanguage(str, Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"


class TestCase(BaseModel):
    """Test case for coding challenge"""
    input: Dict[str, Any] = Field(..., description="Test case input")
    expected_output: Any = Field(..., description="Expected output")
    is_hidden: bool = Field(False, description="Whether this is a hidden test case")
    explanation: Optional[str] = Field(None, description="Explanation of the test case")


class CodingChallenge(BaseModel):
    """Coding challenge model"""
    id: str = Field(..., description="Unique challenge identifier")
    title: str = Field(..., description="Challenge title")
    description: str = Field(..., description="Problem description")
    difficulty: CodingDifficulty = Field(..., description="Challenge difficulty")
    category: CodingCategory = Field(..., description="Challenge category")
    tags: List[str] = Field(default_factory=list, description="Challenge tags")
    time_limit: int = Field(1800, description="Time limit in seconds (30 minutes default)")
    memory_limit: int = Field(256, description="Memory limit in MB")
    test_cases: List[TestCase] = Field(..., description="Test cases for the challenge")
    starter_code: Dict[str, str] = Field(default_factory=dict, description="Starter code by language")
    solution: Dict[str, str] = Field(default_factory=dict, description="Solution code by language")
    hints: List[str] = Field(default_factory=list, description="Hints for solving the problem")
    companies: List[str] = Field(default_factory=list, description="Companies that ask this question")
    frequency: int = Field(1, description="How frequently this question is asked (1-10)")
    
    class Config:
        use_enum_values = True


class CodeSubmission(BaseModel):
    """Code submission model"""
    submission_id: str = Field(..., description="Unique submission identifier")
    challenge_id: str = Field(..., description="Challenge identifier")
    user_id: str = Field(..., description="User identifier")
    language: ProgrammingLanguage = Field(..., description="Programming language used")
    code: str = Field(..., description="Submitted code")
    submitted_at: datetime = Field(default_factory=datetime.utcnow, description="Submission timestamp")
    execution_time: Optional[int] = Field(None, description="Execution time in milliseconds")
    memory_used: Optional[int] = Field(None, description="Memory used in KB")
    status: str = Field("pending", description="Submission status")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TestResult(BaseModel):
    """Test case execution result"""
    test_case_index: int = Field(..., description="Test case index")
    passed: bool = Field(..., description="Whether test case passed")
    input: Dict[str, Any] = Field(..., description="Test input")
    expected_output: Any = Field(..., description="Expected output")
    actual_output: Any = Field(None, description="Actual output")
    execution_time: int = Field(0, description="Execution time in milliseconds")
    memory_used: int = Field(0, description="Memory used in KB")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ExecutionResult(BaseModel):
    """Code execution result"""
    submission_id: str = Field(..., description="Submission identifier")
    success: bool = Field(..., description="Whether execution was successful")
    test_results: List[TestResult] = Field(..., description="Individual test results")
    passed_tests: int = Field(..., description="Number of passed tests")
    total_tests: int = Field(..., description="Total number of tests")
    overall_status: str = Field(..., description="Overall execution status")
    execution_time: int = Field(0, description="Total execution time in milliseconds")
    memory_used: int = Field(0, description="Peak memory used in KB")
    error_message: Optional[str] = Field(None, description="Error message if compilation/execution failed")
    ai_feedback: Optional[str] = Field(None, description="AI-generated feedback on the solution")


class TechnicalInterviewSession(BaseModel):
    """Technical interview session model"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier")
    job_role: str = Field(..., description="Target job role")
    company: Optional[str] = Field(None, description="Target company")
    challenges: List[str] = Field(..., description="List of challenge IDs")
    current_challenge_index: int = Field(0, description="Current challenge index")
    submissions: List[CodeSubmission] = Field(default_factory=list, description="Code submissions")
    status: str = Field("active", description="Session status")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Session start time")
    completed_at: Optional[datetime] = Field(None, description="Session completion time")
    total_score: int = Field(0, description="Total session score")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TechnicalInterviewFeedback(BaseModel):
    """Technical interview feedback"""
    session_id: str = Field(..., description="Session identifier")
    overall_score: int = Field(..., ge=0, le=100, description="Overall score")
    problem_solving_score: int = Field(..., ge=0, le=100, description="Problem solving score")
    code_quality_score: int = Field(..., ge=0, le=100, description="Code quality score")
    efficiency_score: int = Field(..., ge=0, le=100, description="Algorithm efficiency score")
    communication_score: int = Field(..., ge=0, le=100, description="Communication score")
    strengths: List[str] = Field(default_factory=list, description="Identified strengths")
    areas_for_improvement: List[str] = Field(default_factory=list, description="Areas for improvement")
    detailed_feedback: List[Dict[str, Any]] = Field(default_factory=list, description="Challenge-specific feedback")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Feedback generation time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Request/Response schemas for API endpoints
class GetChallengesRequest(BaseModel):
    """Request schema for getting coding challenges"""
    difficulty: Optional[CodingDifficulty] = Field(None, description="Filter by difficulty")
    category: Optional[CodingCategory] = Field(None, description="Filter by category")
    company: Optional[str] = Field(None, description="Filter by company")
    limit: int = Field(20, ge=1, le=100, description="Number of challenges to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class StartTechnicalInterviewRequest(BaseModel):
    """Request schema for starting technical interview"""
    job_role: str = Field(..., description="Target job role")
    company: str = Field("", description="Target company (optional)")
    difficulty: CodingDifficulty = Field(CodingDifficulty.MEDIUM, description="Preferred difficulty")
    categories: List[CodingCategory] = Field(default_factory=list, description="Preferred categories")
    challenge_count: int = Field(3, ge=1, le=5, description="Number of challenges")
    time_limit: int = Field(3600, description="Total time limit in seconds")


class SubmitCodeRequest(BaseModel):
    """Request schema for code submission"""
    session_id: str = Field(..., description="Technical interview session ID")
    challenge_id: str = Field(..., description="Challenge ID")
    language: ProgrammingLanguage = Field(..., description="Programming language")
    code: str = Field(..., description="Code solution")


class ExecuteCodeRequest(BaseModel):
    """Request schema for code execution"""
    challenge_id: str = Field(..., description="Challenge ID")
    language: ProgrammingLanguage = Field(..., description="Programming language")
    code: str = Field(..., description="Code to execute")
    test_cases: Optional[List[TestCase]] = Field(None, description="Custom test cases")


class GetTechnicalFeedbackRequest(BaseModel):
    """Request schema for getting technical interview feedback"""
    session_id: str = Field(..., description="Technical interview session ID")


# Response schemas
class ChallengesResponse(BaseModel):
    """Response schema for challenges"""
    success: bool = Field(..., description="Success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")


class TechnicalInterviewResponse(BaseModel):
    """Response schema for technical interview operations"""
    success: bool = Field(..., description="Success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")


class CodeExecutionResponse(BaseModel):
    """Response schema for code execution"""
    success: bool = Field(..., description="Success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")