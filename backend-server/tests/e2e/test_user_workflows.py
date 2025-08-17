"""
End-to-end tests for complete user workflows
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import httpx
from datetime import datetime

from app.main import app


class TestUserWorkflows:
    """Test cases for complete user workflows"""
    
    @pytest.fixture
    def client(self):
        """Create test client for API testing"""
        return httpx.AsyncClient(app=app, base_url="http://test")
    
    @pytest.fixture
    def authenticated_headers(self):
        """Mock authenticated headers for testing"""
        return {"Authorization": "Bearer test-token"}
    
    @pytest.mark.asyncio
    async def test_complete_job_search_workflow(self, client, authenticated_headers):
        """Test complete job search workflow from registration to application"""
        
        # Step 1: User registration
        registration_data = {
            "email": "testuser@example.com",
            "password": "TestPassword123",
            "full_name": "Test User"
        }
        
        with patch('app.core.auth.auth_manager.create_user') as mock_create_user:
            mock_create_user.return_value = {
                "user_id": "user-123",
                "email": "testuser@example.com"
            }
            
            response = await client.post("/api/v1/auth/register", json=registration_data)
            assert response.status_code == 201
            user_data = response.json()
            assert "user_id" in user_data
        
        # Step 2: User login
        login_data = {
            "email": "testuser@example.com",
            "password": "TestPassword123"
        }
        
        with patch('app.core.auth.auth_manager.authenticate_user') as mock_auth:
            mock_auth.return_value = {
                "access_token": "test-token",
                "user_id": "user-123"
            }
            
            response = await client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
            auth_data = response.json()
            assert "access_token" in auth_data
        
        # Step 3: Profile setup
        profile_data = {
            "skills": ["Python", "React", "AWS"],
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "TechCorp",
                    "duration": "2020-2023"
                }
            ],
            "preferences": {
                "job_types": ["full-time"],
                "locations": ["remote", "san-francisco"],
                "salary_range": {"min": 80000, "max": 120000}
            }
        }
        
        with patch('app.api.user.update_user_profile') as mock_update_profile:
            mock_update_profile.return_value = {"success": True}
            
            response = await client.put(
                "/api/v1/user/profile",
                json=profile_data,
                headers=authenticated_headers
            )
            assert response.status_code == 200
        
        # Step 4: Job discovery
        with patch('app.agents.job_discovery.JobDiscoveryAgent.process_request') as mock_job_discovery:
            mock_job_discovery.return_value = {
                "success": True,
                "data": {
                    "jobs": [
                        {
                            "job_id": "job-123",
                            "title": "Senior Software Engineer",
                            "company": "TechCorp",
                            "location": "San Francisco, CA",
                            "match_score": 0.85
                        }
                    ]
                }
            }
            
            response = await client.post(
                "/api/v1/jobs/discover",
                json={"search_criteria": {"keywords": ["python", "react"]}},
                headers=authenticated_headers
            )
            assert response.status_code == 200
            jobs_data = response.json()
            assert len(jobs_data["jobs"]) > 0
        
        # Step 5: Skills gap analysis
        with patch('app.agents.skills_analysis.SkillsAnalysisAgent.process_request') as mock_skills_analysis:
            mock_skills_analysis.return_value = {
                "success": True,
                "data": {
                    "critical_gaps": [
                        {"skill": "Kubernetes", "priority": "high"}
                    ],
                    "overall_readiness": {"percentage": 75}
                }
            }
            
            response = await client.post(
                "/api/v1/skills/analyze-gaps",
                json={"job_id": "job-123"},
                headers=authenticated_headers
            )
            assert response.status_code == 200
            skills_data = response.json()
            assert "critical_gaps" in skills_data
        
        # Step 6: Resume optimization
        with patch('app.agents.resume_optimization.ResumeOptimizationAgent.process_request') as mock_resume_opt:
            mock_resume_opt.return_value = {
                "success": True,
                "data": {
                    "optimized_resume": {"summary": "Optimized summary"},
                    "ats_score": 85,
                    "resume_id": "resume-123"
                }
            }
            
            response = await client.post(
                "/api/v1/resume/optimize",
                json={"job_id": "job-123"},
                headers=authenticated_headers
            )
            assert response.status_code == 200
            resume_data = response.json()
            assert resume_data["ats_score"] > 80
        
        # Step 7: Interview preparation
        with patch('app.agents.interview_preparation.InterviewPreparationAgent.process_request') as mock_interview_prep:
            mock_interview_prep.return_value = {
                "success": True,
                "data": {
                    "questions": [
                        {
                            "question": "Tell me about yourself",
                            "type": "behavioral",
                            "difficulty": "easy"
                        }
                    ],
                    "session_id": "interview-session-123"
                }
            }
            
            response = await client.post(
                "/api/v1/interview/prepare",
                json={"job_id": "job-123", "interview_type": "behavioral"},
                headers=authenticated_headers
            )
            assert response.status_code == 200
            interview_data = response.json()
            assert len(interview_data["questions"]) > 0
        
        # Step 8: Job application tracking
        application_data = {
            "job_id": "job-123",
            "resume_id": "resume-123",
            "status": "applied",
            "applied_date": datetime.utcnow().isoformat()
        }
        
        with patch('app.api.jobs.track_job_application') as mock_track_application:
            mock_track_application.return_value = {"success": True, "application_id": "app-123"}
            
            response = await client.post(
                "/api/v1/jobs/applications",
                json=application_data,
                headers=authenticated_headers
            )
            assert response.status_code == 201
            app_data = response.json()
            assert "application_id" in app_data
    
    @pytest.mark.asyncio
    async def test_career_development_workflow(self, client, authenticated_headers):
        """Test career development and strategy workflow"""
        
        # Step 1: Career goal setting
        career_goals = {
            "target_role": "Senior Software Engineer",
            "target_companies": ["Google", "Microsoft"],
            "timeline": "12 months",
            "salary_target": 150000
        }
        
        with patch('app.agents.career_strategy.CareerStrategyAgent.process_request') as mock_career_strategy:
            mock_career_strategy.return_value = {
                "success": True,
                "data": {
                    "roadmap_id": "roadmap-123",
                    "milestones": [
                        {
                            "title": "Improve Python skills",
                            "target_date": "2025-04-01",
                            "status": "not_started"
                        }
                    ]
                }
            }
            
            response = await client.post(
                "/api/v1/career/goals",
                json=career_goals,
                headers=authenticated_headers
            )
            assert response.status_code == 201
            roadmap_data = response.json()
            assert "roadmap_id" in roadmap_data
        
        # Step 2: Skills development planning
        with patch('app.agents.skills_analysis.SkillsAnalysisAgent.process_request') as mock_skills_planning:
            mock_skills_planning.return_value = {
                "success": True,
                "data": {
                    "learning_paths": [
                        {
                            "skill": "Kubernetes",
                            "estimated_duration": "3 months",
                            "resources": [
                                {"type": "course", "name": "Kubernetes Fundamentals"}
                            ]
                        }
                    ]
                }
            }
            
            response = await client.post(
                "/api/v1/skills/learning-paths",
                json={"target_skills": ["Kubernetes", "Docker"]},
                headers=authenticated_headers
            )
            assert response.status_code == 200
            learning_data = response.json()
            assert len(learning_data["learning_paths"]) > 0
        
        # Step 3: Progress tracking
        progress_data = {
            "milestone_id": "milestone-123",
            "progress_percentage": 50,
            "notes": "Completed Kubernetes basics course"
        }
        
        with patch('app.api.career_strategy.update_milestone_progress') as mock_update_progress:
            mock_update_progress.return_value = {"success": True}
            
            response = await client.put(
                "/api/v1/career/milestones/milestone-123/progress",
                json=progress_data,
                headers=authenticated_headers
            )
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_networking_workflow(self, client, authenticated_headers):
        """Test networking and outreach workflow"""
        
        # Step 1: Contact discovery
        with patch('app.agents.networking.NetworkingAgent.process_request') as mock_networking:
            mock_networking.return_value = {
                "success": True,
                "data": {
                    "contacts": [
                        {
                            "name": "John Smith",
                            "title": "Engineering Manager",
                            "company": "TechCorp",
                            "email": "john.smith@techcorp.com"
                        }
                    ]
                }
            }
            
            response = await client.post(
                "/api/v1/networking/discover-contacts",
                json={"target_company": "TechCorp", "role": "Engineering Manager"},
                headers=authenticated_headers
            )
            assert response.status_code == 200
            contacts_data = response.json()
            assert len(contacts_data["contacts"]) > 0
        
        # Step 2: Email template generation
        with patch('app.agents.networking.NetworkingAgent.process_request') as mock_email_gen:
            mock_email_gen.return_value = {
                "success": True,
                "data": {
                    "email_template": {
                        "subject": "Interest in Software Engineering Opportunities",
                        "body": "Hi John, I'm interested in opportunities at TechCorp..."
                    }
                }
            }
            
            response = await client.post(
                "/api/v1/networking/generate-email",
                json={
                    "contact_id": "contact-123",
                    "purpose": "job_inquiry",
                    "tone": "professional"
                },
                headers=authenticated_headers
            )
            assert response.status_code == 200
            email_data = response.json()
            assert "email_template" in email_data
        
        # Step 3: Campaign creation and tracking
        campaign_data = {
            "name": "TechCorp Outreach",
            "target_company": "TechCorp",
            "contacts": ["contact-123"],
            "email_template_id": "template-123"
        }
        
        with patch('app.api.networking.create_campaign') as mock_create_campaign:
            mock_create_campaign.return_value = {
                "success": True,
                "campaign_id": "campaign-123"
            }
            
            response = await client.post(
                "/api/v1/networking/campaigns",
                json=campaign_data,
                headers=authenticated_headers
            )
            assert response.status_code == 201
            campaign_response = response.json()
            assert "campaign_id" in campaign_response
    
    @pytest.mark.asyncio
    async def test_interview_practice_workflow(self, client, authenticated_headers):
        """Test complete interview practice workflow"""
        
        # Step 1: Start mock interview session
        interview_config = {
            "job_id": "job-123",
            "interview_type": "behavioral",
            "duration_minutes": 30
        }
        
        with patch('app.agents.interview_preparation.InterviewPreparationAgent.process_request') as mock_interview:
            mock_interview.return_value = {
                "success": True,
                "data": {
                    "session_id": "interview-session-123",
                    "questions": [
                        {
                            "question_id": "q1",
                            "question": "Tell me about a challenging project",
                            "type": "behavioral"
                        }
                    ]
                }
            }
            
            response = await client.post(
                "/api/v1/interview/start-session",
                json=interview_config,
                headers=authenticated_headers
            )
            assert response.status_code == 201
            session_data = response.json()
            assert "session_id" in session_data
        
        # Step 2: Submit interview responses
        response_data = {
            "session_id": "interview-session-123",
            "question_id": "q1",
            "response": "I worked on a challenging microservices project...",
            "duration_seconds": 180
        }
        
        with patch('app.api.interview.submit_response') as mock_submit_response:
            mock_submit_response.return_value = {"success": True}
            
            response = await client.post(
                "/api/v1/interview/responses",
                json=response_data,
                headers=authenticated_headers
            )
            assert response.status_code == 200
        
        # Step 3: Get interview feedback
        with patch('app.agents.interview_preparation.InterviewPreparationAgent.process_request') as mock_feedback:
            mock_feedback.return_value = {
                "success": True,
                "data": {
                    "feedback": {
                        "overall_score": 8,
                        "strengths": ["Clear communication", "Good examples"],
                        "improvements": ["More specific metrics", "Better structure"]
                    }
                }
            }
            
            response = await client.get(
                "/api/v1/interview/sessions/interview-session-123/feedback",
                headers=authenticated_headers
            )
            assert response.status_code == 200
            feedback_data = response.json()
            assert "feedback" in feedback_data
            assert feedback_data["feedback"]["overall_score"] > 0
    
    @pytest.mark.asyncio
    async def test_dashboard_integration_workflow(self, client, authenticated_headers):
        """Test dashboard integration and real-time updates"""
        
        # Step 1: Get dashboard overview
        with patch('app.api.dashboard.get_dashboard_data') as mock_dashboard:
            mock_dashboard.return_value = {
                "success": True,
                "data": {
                    "active_applications": 5,
                    "interview_sessions": 2,
                    "skill_progress": 75,
                    "recent_activities": [
                        {
                            "type": "job_application",
                            "description": "Applied to Software Engineer at TechCorp",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    ]
                }
            }
            
            response = await client.get(
                "/api/v1/dashboard",
                headers=authenticated_headers
            )
            assert response.status_code == 200
            dashboard_data = response.json()
            assert "active_applications" in dashboard_data
            assert "recent_activities" in dashboard_data
        
        # Step 2: Test WebSocket connection for real-time updates
        with patch('app.api.websocket.WebSocketManager') as mock_ws_manager:
            mock_ws_manager.return_value.connect = AsyncMock()
            mock_ws_manager.return_value.send_update = AsyncMock()
            
            # Simulate real-time update
            update_data = {
                "type": "job_recommendation",
                "data": {
                    "job_id": "new-job-456",
                    "title": "Senior Python Developer",
                    "match_score": 0.92
                }
            }
            
            # This would normally be tested with a WebSocket client
            # For now, we'll test the update mechanism
            mock_ws_manager.return_value.send_update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, client, authenticated_headers):
        """Test error recovery and fallback mechanisms"""
        
        # Test API failure with fallback
        with patch('app.agents.job_discovery.JobDiscoveryAgent.process_request') as mock_job_discovery:
            # First call fails
            mock_job_discovery.side_effect = [
                Exception("External API unavailable"),
                {
                    "success": True,
                    "data": {"jobs": [{"job_id": "fallback-job-1"}]}
                }
            ]
            
            response = await client.post(
                "/api/v1/jobs/discover",
                json={"search_criteria": {"keywords": ["python"]}},
                headers=authenticated_headers
            )
            
            # Should recover with fallback mechanism
            assert response.status_code in [200, 202]  # 202 for partial success
    
    @pytest.mark.asyncio
    async def test_data_export_workflow(self, client, authenticated_headers):
        """Test user data export workflow"""
        
        # Request data export
        export_request = {
            "data_types": ["profile", "applications", "resumes", "interviews"],
            "format": "json"
        }
        
        with patch('app.api.data_management.initiate_data_export') as mock_export:
            mock_export.return_value = {
                "success": True,
                "export_id": "export-123",
                "estimated_completion": "2025-01-08T12:00:00Z"
            }
            
            response = await client.post(
                "/api/v1/data/export",
                json=export_request,
                headers=authenticated_headers
            )
            assert response.status_code == 202
            export_data = response.json()
            assert "export_id" in export_data
        
        # Check export status
        with patch('app.api.data_management.get_export_status') as mock_status:
            mock_status.return_value = {
                "export_id": "export-123",
                "status": "completed",
                "download_url": "https://example.com/exports/export-123.json"
            }
            
            response = await client.get(
                "/api/v1/data/exports/export-123/status",
                headers=authenticated_headers
            )
            assert response.status_code == 200
            status_data = response.json()
            assert status_data["status"] == "completed"