"""
Pytest configuration and shared fixtures for JobSwitch.ai testing
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.core.config import Settings
from app.models.user import UserProfile
from app.models.job import Job
from app.models.resume import Resume
from app.models.interview import InterviewSession
from app.models.networking import NetworkingCampaign
from app.models.career_strategy import CareerRoadmap


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock application settings for testing"""
    return Settings(
        secret_key="test-secret-key",
        database_url="sqlite:///test.db",
        watsonx_api_key="test-watsonx-key",
        watsonx_project_id="test-project-id",
        redis_url="redis://localhost:6379/1",
        environment="test"
    )


@pytest.fixture
def mock_watsonx_client():
    """Mock WatsonX client for testing"""
    client = AsyncMock()
    
    async def mock_generate_text(prompt: str, model_id: str = "mock-model", **kwargs):
        """Mock text generation with realistic responses"""
        if "extract" in prompt.lower() and "skills" in prompt.lower():
            return {
                "success": True,
                "generated_text": '{"technical_skills": [{"name": "Python", "proficiency": "advanced"}], "soft_skills": [{"name": "Leadership", "proficiency": "intermediate"}]}'
            }
        elif "job" in prompt.lower() and "recommendation" in prompt.lower():
            return {
                "success": True,
                "generated_text": '{"recommendations": [{"title": "Software Engineer", "company": "TechCorp", "match_score": 0.85}]}'
            }
        elif "resume" in prompt.lower() and "optimize" in prompt.lower():
            return {
                "success": True,
                "generated_text": '{"optimized_content": "Optimized resume content", "ats_score": 85, "improvements": ["Added keywords", "Improved formatting"]}'
            }
        elif "interview" in prompt.lower() and "question" in prompt.lower():
            return {
                "success": True,
                "generated_text": '{"questions": [{"question": "Tell me about yourself", "type": "behavioral", "difficulty": "easy"}]}'
            }
        elif "feedback" in prompt.lower():
            return {
                "success": True,
                "generated_text": '{"overall_score": 8, "strengths": ["Clear communication"], "improvements": ["More specific examples"]}'
            }
        else:
            return {
                "success": True,
                "generated_text": f"Mock response for: {prompt[:50]}..."
            }
    
    client.generate_text = mock_generate_text
    return client


@pytest.fixture
def mock_langchain_manager():
    """Mock LangChain manager for testing"""
    manager = AsyncMock()
    
    async def mock_process_with_chain(chain: str, input_data: Dict[str, Any]):
        return {
            "success": True,
            "result": f"Mock LangChain result for {chain}",
            "processing_time_ms": 100
        }
    
    manager.process_with_chain = mock_process_with_chain
    manager.available = True
    return manager


@pytest.fixture
def mock_database():
    """Mock database session for testing"""
    db = Mock()
    
    # Mock query methods
    db.query.return_value = db
    db.filter.return_value = db
    db.first.return_value = None
    db.all.return_value = []
    db.add.return_value = None
    db.commit.return_value = None
    db.rollback.return_value = None
    db.close.return_value = None
    
    return db


@pytest.fixture
def sample_user_profile():
    """Sample user profile for testing"""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "full_name": "Test User",
        "skills": [
            {"name": "Python", "category": "programming", "proficiency": "advanced", "years_experience": 5},
            {"name": "React", "category": "frontend", "proficiency": "intermediate", "years_experience": 3}
        ],
        "experience": [
            {
                "title": "Software Engineer",
                "company": "TechCorp",
                "duration": "2020-2023",
                "description": "Developed web applications using Python and React"
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Computer Science",
                "institution": "Tech University",
                "year": 2020
            }
        ],
        "preferences": {
            "job_types": ["full-time"],
            "locations": ["remote", "san-francisco"],
            "salary_range": {"min": 80000, "max": 120000}
        },
        "career_goals": {
            "target_role": "Senior Software Engineer",
            "target_companies": ["Google", "Microsoft"],
            "timeline": "6-12 months"
        }
    }


@pytest.fixture
def sample_job_posting():
    """Sample job posting for testing"""
    return {
        "job_id": "job-123",
        "title": "Senior Software Engineer",
        "company": "TechCorp",
        "location": "San Francisco, CA",
        "description": "We are looking for a Senior Software Engineer with 5+ years of experience in Python and React...",
        "requirements": [
            "5+ years of Python experience",
            "3+ years of React experience",
            "Experience with cloud platforms (AWS/GCP)",
            "Strong problem-solving skills"
        ],
        "salary_range": {"min": 100000, "max": 150000},
        "posted_date": datetime.utcnow().isoformat(),
        "source": "linkedin"
    }


@pytest.fixture
def sample_resume():
    """Sample resume for testing"""
    return {
        "resume_id": "resume-123",
        "user_id": "test-user-123",
        "version": 1,
        "content": {
            "personal_info": {
                "name": "Test User",
                "email": "test@example.com",
                "phone": "+1-555-0123"
            },
            "summary": "Experienced software engineer with 5+ years in web development",
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "TechCorp",
                    "duration": "2020-2023",
                    "achievements": [
                        "Developed 10+ web applications using Python and React",
                        "Improved system performance by 30%"
                    ]
                }
            ],
            "skills": ["Python", "React", "AWS", "PostgreSQL"],
            "education": [
                {
                    "degree": "Bachelor of Computer Science",
                    "institution": "Tech University",
                    "year": 2020
                }
            ]
        },
        "target_job_id": "job-123",
        "ats_score": 75,
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_interview_session():
    """Sample interview session for testing"""
    return {
        "session_id": "interview-123",
        "user_id": "test-user-123",
        "job_role": "Senior Software Engineer",
        "questions": [
            {
                "question": "Tell me about yourself",
                "type": "behavioral",
                "difficulty": "easy"
            },
            {
                "question": "Describe a challenging project you worked on",
                "type": "behavioral",
                "difficulty": "medium"
            }
        ],
        "responses": [
            {
                "question_id": 0,
                "response": "I am a software engineer with 5 years of experience...",
                "duration_seconds": 120
            }
        ],
        "feedback": {
            "overall_score": 8,
            "strengths": ["Clear communication", "Good examples"],
            "improvements": ["More specific metrics", "Better structure"]
        },
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_networking_campaign():
    """Sample networking campaign for testing"""
    return {
        "campaign_id": "campaign-123",
        "user_id": "test-user-123",
        "target_company": "TechCorp",
        "contacts": [
            {
                "name": "John Smith",
                "title": "Engineering Manager",
                "email": "john.smith@techcorp.com",
                "linkedin_url": "https://linkedin.com/in/johnsmith"
            }
        ],
        "email_templates": [
            {
                "subject": "Interest in Software Engineering Opportunities",
                "body": "Hi {name}, I'm interested in opportunities at {company}..."
            }
        ],
        "sent_emails": [
            {
                "contact_id": 0,
                "sent_at": datetime.utcnow().isoformat(),
                "status": "sent"
            }
        ],
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_career_roadmap():
    """Sample career roadmap for testing"""
    return {
        "roadmap_id": "roadmap-123",
        "user_id": "test-user-123",
        "current_role": "Software Engineer",
        "target_role": "Senior Software Engineer",
        "milestones": [
            {
                "title": "Improve Python skills",
                "description": "Complete advanced Python course",
                "target_date": (datetime.utcnow() + timedelta(days=90)).isoformat(),
                "status": "in_progress"
            },
            {
                "title": "Get AWS certification",
                "description": "Complete AWS Solutions Architect certification",
                "target_date": (datetime.utcnow() + timedelta(days=180)).isoformat(),
                "status": "not_started"
            }
        ],
        "skills_to_develop": [
            {"name": "AWS", "priority": "high", "estimated_time": "3 months"},
            {"name": "Kubernetes", "priority": "medium", "estimated_time": "2 months"}
        ],
        "timeline": "6-12 months",
        "progress": 25.0,
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def mock_external_apis():
    """Mock external API responses"""
    return {
        "linkedin": {
            "jobs": [
                {
                    "id": "linkedin-job-1",
                    "title": "Software Engineer",
                    "company": "LinkedIn Corp",
                    "location": "San Francisco, CA"
                }
            ]
        },
        "indeed": {
            "jobs": [
                {
                    "id": "indeed-job-1",
                    "title": "Python Developer",
                    "company": "Indeed Inc",
                    "location": "Austin, TX"
                }
            ]
        },
        "glassdoor": {
            "jobs": [
                {
                    "id": "glassdoor-job-1",
                    "title": "Full Stack Developer",
                    "company": "Glassdoor",
                    "location": "Remote"
                }
            ]
        }
    }


@pytest.fixture
def performance_thresholds():
    """Performance testing thresholds"""
    return {
        "ai_response_time_ms": 5000,  # 5 seconds max for AI responses
        "api_response_time_ms": 1000,  # 1 second max for API responses
        "database_query_time_ms": 500,  # 500ms max for database queries
        "concurrent_users": 100,  # Support 100 concurrent users
        "memory_usage_mb": 512,  # Max 512MB memory usage
        "cpu_usage_percent": 80  # Max 80% CPU usage
    }


# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Automatically cleanup test data after each test"""
    yield
    # Cleanup logic would go here
    # For now, we'll just pass since we're using mocks
    pass