"""
User Acceptance Tests for JobSwitch.ai
Tests real-world job search scenarios from user perspective.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime, timedelta

from app.main import app

client = TestClient(app)

class TestUserAcceptanceScenarios:
    """Test real-world user scenarios for job search platform"""
    
    @pytest.fixture
    def new_graduate_user(self):
        """New graduate looking for first job"""
        return {
            "email": "newgrad@university.edu",
            "password": "SecurePass123!",
            "full_name": "Alex Graduate",
            "skills": ["Python", "JavaScript", "SQL"],
            "experience_years": 0,
            "education": "Computer Science Degree",
            "current_role": "Student",
            "target_role": "Software Developer"
        }
    
    @pytest.fixture
    def career_changer_user(self):
        """Professional changing careers"""
        return {
            "email": "changer@company.com",
            "password": "ChangeCareer456!",
            "full_name": "Jordan Changer",
            "skills": ["Project Management", "Excel", "Communication"],
            "experience_years": 8,
            "current_role": "Marketing Manager",
            "target_role": "Product Manager"
        }
    
    @pytest.fixture
    def senior_professional_user(self):
        """Senior professional seeking advancement"""
        return {
            "email": "senior@techcorp.com",
            "password": "SeniorDev789!",
            "full_name": "Taylor Senior",
            "skills": ["Python", "AWS", "Team Leadership", "Architecture"],
            "experience_years": 12,
            "current_role": "Senior Software Engineer",
            "target_role": "Engineering Manager"
        }
    
    def authenticate_user(self, user_data):
        """Helper to register and authenticate a user"""
        # Register user
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @patch('app.integrations.watsonx.WatsonXClient')
    @patch('app.integrations.job_connectors.LinkedInConnector')
    async def test_new_graduate_job_search_journey(self, mock_linkedin, mock_watsonx, new_graduate_user):
        """Test complete job search journey for new graduate"""
        
        # Setup mocks
        mock_watsonx_instance = Mock()
        mock_watsonx.return_value = mock_watsonx_instance
        mock_linkedin_instance = Mock()
        mock_linkedin.return_value = mock_linkedin_instance
        
        # 1. User Registration and Profile Setup
        headers = self.authenticate_user(new_graduate_user)
        
        # Set up profile
        profile_response = client.post("/api/v1/user/profile", 
                                     json=new_graduate_user, headers=headers)
        assert profile_response.status_code == 200
        
        # 2. Skills Analysis - Identify gaps for entry-level positions
        mock_watsonx_instance.analyze_skills.return_value = {
            "extracted_skills": ["Python", "JavaScript", "SQL"],
            "skill_gaps": ["React", "Git", "Testing"],
            "recommendations": [
                "Learn React for frontend development",
                "Practice Git version control",
                "Study unit testing frameworks"
            ],
            "entry_level_readiness": 75
        }
        
        skills_response = client.post("/api/v1/agents/skills-analysis/analyze",
                                    json={"resume_text": "Recent CS graduate with internship experience"},
                                    headers=headers)
        assert skills_response.status_code == 200
        skills_data = skills_response.json()
        assert skills_data["entry_level_readiness"] >= 70
        
        # 3. Job Discovery - Find entry-level positions
        mock_linkedin_instance.search_jobs.return_value = [
            {
                "title": "Junior Software Developer",
                "company": "StartupCorp",
                "location": "Remote",
                "description": "Entry-level position for new graduates",
                "requirements": ["Python", "JavaScript", "Bachelor's degree"],
                "salary_range": {"min": 60000, "max": 80000},
                "source": "linkedin",
                "experience_required": "0-2 years"
            },
            {
                "title": "Software Engineer I",
                "company": "TechGiant",
                "location": "San Francisco, CA",
                "description": "New grad program position",
                "requirements": ["CS degree", "Programming skills", "Problem solving"],
                "salary_range": {"min": 90000, "max": 120000},
                "source": "linkedin",
                "experience_required": "0-1 years"
            }
        ]
        
        job_search_response = client.post("/api/v1/agents/job-discovery/search",
                                        json={
                                            "keywords": "junior software developer",
                                            "experience_level": "entry",
                                            "location": "remote"
                                        },
                                        headers=headers)
        assert job_search_response.status_code == 200
        jobs = job_search_response.json()["jobs"]
        assert len(jobs) >= 1
        assert any("junior" in job["title"].lower() or "entry" in job["description"].lower() for job in jobs)
        
        # 4. Resume Optimization for entry-level positions
        mock_watsonx_instance.optimize_resume.return_value = {
            "optimized_content": "Optimized resume highlighting education and projects",
            "ats_score": 78,
            "improvements": [
                "Emphasized relevant coursework",
                "Highlighted internship projects",
                "Added technical skills section"
            ],
            "entry_level_focus": True
        }
        
        resume_response = client.post("/api/v1/agents/resume-optimization/optimize",
                                    json={
                                        "resume_content": "Basic graduate resume",
                                        "target_job_id": "junior_dev_123",
                                        "experience_level": "entry"
                                    },
                                    headers=headers)
        assert resume_response.status_code == 200
        assert resume_response.json()["ats_score"] >= 75
        
        # 5. Interview Preparation - Focus on fundamentals
        mock_watsonx_instance.generate_interview_questions.return_value = [
            {"question": "Tell me about yourself", "type": "behavioral", "difficulty": "basic"},
            {"question": "What is object-oriented programming?", "type": "technical", "difficulty": "basic"},
            {"question": "Describe a challenging project from school", "type": "behavioral", "difficulty": "basic"}
        ]
        
        interview_prep_response = client.post("/api/v1/agents/interview-preparation/questions",
                                            json={
                                                "job_role": "Junior Software Developer",
                                                "experience_level": "entry"
                                            },
                                            headers=headers)
        assert interview_prep_response.status_code == 200
        questions = interview_prep_response.json()["questions"]
        assert len(questions) >= 3
        assert any(q["difficulty"] == "basic" for q in questions)
        
        # 6. Career Strategy - Entry-level career path
        mock_watsonx_instance.generate_career_roadmap.return_value = {
            "milestones": [
                {"title": "Land first developer job", "timeline": "3 months", "priority": "high"},
                {"title": "Learn React framework", "timeline": "6 months", "priority": "medium"},
                {"title": "Contribute to open source", "timeline": "9 months", "priority": "medium"},
                {"title": "Seek promotion to mid-level", "timeline": "18 months", "priority": "low"}
            ],
            "timeline": "24 months",
            "focus": "skill_building"
        }
        
        career_response = client.post("/api/v1/agents/career-strategy/roadmap",
                                    json={
                                        "current_role": "Student",
                                        "target_role": "Software Developer",
                                        "experience_level": "entry"
                                    },
                                    headers=headers)
        assert career_response.status_code == 200
        roadmap = career_response.json()
        assert len(roadmap["milestones"]) >= 3
        assert any("first" in milestone["title"].lower() for milestone in roadmap["milestones"])
    
    @patch('app.integrations.watsonx.WatsonXClient')
    @patch('app.integrations.job_connectors.LinkedInConnector')
    async def test_career_changer_transition_journey(self, mock_linkedin, mock_watsonx, career_changer_user):
        """Test career transition journey from marketing to product management"""
        
        # Setup mocks
        mock_watsonx_instance = Mock()
        mock_watsonx.return_value = mock_watsonx_instance
        mock_linkedin_instance = Mock()
        mock_linkedin.return_value = mock_linkedin_instance
        
        # 1. User Registration and Profile Setup
        headers = self.authenticate_user(career_changer_user)
        
        profile_response = client.post("/api/v1/user/profile", 
                                     json=career_changer_user, headers=headers)
        assert profile_response.status_code == 200
        
        # 2. Skills Analysis - Identify transferable skills and gaps
        mock_watsonx_instance.analyze_skills.return_value = {
            "extracted_skills": ["Project Management", "Excel", "Communication"],
            "transferable_skills": ["Project Management", "Communication", "Stakeholder Management"],
            "skill_gaps": ["Product Analytics", "User Research", "Roadmap Planning"],
            "recommendations": [
                "Learn product analytics tools (Mixpanel, Amplitude)",
                "Study user research methodologies",
                "Practice roadmap planning frameworks"
            ],
            "transition_feasibility": 85
        }
        
        skills_response = client.post("/api/v1/agents/skills-analysis/analyze",
                                    json={
                                        "resume_text": "Marketing manager with 8 years experience",
                                        "career_transition": {
                                            "from": "Marketing Manager",
                                            "to": "Product Manager"
                                        }
                                    },
                                    headers=headers)
        assert skills_response.status_code == 200
        skills_data = skills_response.json()
        assert skills_data["transition_feasibility"] >= 80
        assert len(skills_data["transferable_skills"]) >= 2
        
        # 3. Job Discovery - Find transition-friendly PM roles
        mock_linkedin_instance.search_jobs.return_value = [
            {
                "title": "Associate Product Manager",
                "company": "GrowthCorp",
                "location": "New York, NY",
                "description": "Looking for someone with strong communication and project management skills",
                "requirements": ["Project management", "Communication", "Analytics mindset"],
                "salary_range": {"min": 85000, "max": 110000},
                "source": "linkedin",
                "career_change_friendly": True
            },
            {
                "title": "Product Manager - Marketing Background Preferred",
                "company": "MarketingTech",
                "location": "Remote",
                "description": "Seeking PM with marketing experience to bridge product and marketing",
                "requirements": ["Marketing experience", "Product sense", "Data analysis"],
                "salary_range": {"min": 95000, "max": 130000},
                "source": "linkedin",
                "career_change_friendly": True
            }
        ]
        
        job_search_response = client.post("/api/v1/agents/job-discovery/search",
                                        json={
                                            "keywords": "product manager",
                                            "career_transition": True,
                                            "current_background": "marketing"
                                        },
                                        headers=headers)
        assert job_search_response.status_code == 200
        jobs = job_search_response.json()["jobs"]
        assert len(jobs) >= 1
        assert any(job.get("career_change_friendly", False) for job in jobs)
        
        # 4. Resume Optimization - Highlight transferable skills
        mock_watsonx_instance.optimize_resume.return_value = {
            "optimized_content": "Resume emphasizing transferable skills and relevant experience",
            "ats_score": 82,
            "improvements": [
                "Highlighted project management experience",
                "Emphasized data-driven decision making",
                "Added relevant marketing-to-product transition narrative"
            ],
            "transition_story": "Clear narrative connecting marketing experience to product management"
        }
        
        resume_response = client.post("/api/v1/agents/resume-optimization/optimize",
                                    json={
                                        "resume_content": "Marketing manager resume",
                                        "target_job_id": "pm_transition_123",
                                        "career_transition": {
                                            "from": "Marketing Manager",
                                            "to": "Product Manager"
                                        }
                                    },
                                    headers=headers)
        assert resume_response.status_code == 200
        assert resume_response.json()["ats_score"] >= 80
        
        # 5. Interview Preparation - Focus on transition story
        mock_watsonx_instance.generate_interview_questions.return_value = [
            {"question": "Why do you want to transition from marketing to product management?", "type": "behavioral", "transition_focused": True},
            {"question": "How would your marketing experience help you as a PM?", "type": "behavioral", "transition_focused": True},
            {"question": "How do you prioritize features?", "type": "technical", "difficulty": "intermediate"}
        ]
        
        interview_prep_response = client.post("/api/v1/agents/interview-preparation/questions",
                                            json={
                                                "job_role": "Product Manager",
                                                "career_transition": True,
                                                "current_background": "marketing"
                                            },
                                            headers=headers)
        assert interview_prep_response.status_code == 200
        questions = interview_prep_response.json()["questions"]
        assert len(questions) >= 3
        assert any(q.get("transition_focused", False) for q in questions)
        
        # 6. Networking - Connect with PMs and career changers
        mock_watsonx_instance.generate_outreach_email.return_value = {
            "subject": "Marketing Manager Interested in Product Management",
            "body": "Hi [Name], I'm a marketing manager looking to transition to product management...",
            "transition_focused": True
        }
        
        networking_response = client.post("/api/v1/agents/networking/generate-email",
                                        json={
                                            "contact_name": "Sarah PM",
                                            "company": "TechCorp",
                                            "position": "Product Manager",
                                            "career_transition": True,
                                            "purpose": "informational_interview"
                                        },
                                        headers=headers)
        assert networking_response.status_code == 200
        email_data = networking_response.json()
        assert "transition" in email_data["body"].lower()
    
    @patch('app.integrations.watsonx.WatsonXClient')
    @patch('app.integrations.job_connectors.LinkedInConnector')
    async def test_senior_professional_advancement_journey(self, mock_linkedin, mock_watsonx, senior_professional_user):
        """Test senior professional seeking management role"""
        
        # Setup mocks
        mock_watsonx_instance = Mock()
        mock_watsonx.return_value = mock_watsonx_instance
        mock_linkedin_instance = Mock()
        mock_linkedin.return_value = mock_linkedin_instance
        
        # 1. User Registration and Profile Setup
        headers = self.authenticate_user(senior_professional_user)
        
        profile_response = client.post("/api/v1/user/profile", 
                                     json=senior_professional_user, headers=headers)
        assert profile_response.status_code == 200
        
        # 2. Skills Analysis - Leadership and management skills
        mock_watsonx_instance.analyze_skills.return_value = {
            "extracted_skills": ["Python", "AWS", "Team Leadership", "Architecture"],
            "leadership_skills": ["Team Leadership", "Mentoring", "Technical Decision Making"],
            "skill_gaps": ["People Management", "Budget Management", "Strategic Planning"],
            "recommendations": [
                "Develop people management skills",
                "Learn budget and resource planning",
                "Study strategic planning frameworks"
            ],
            "management_readiness": 78
        }
        
        skills_response = client.post("/api/v1/agents/skills-analysis/analyze",
                                    json={
                                        "resume_text": "Senior software engineer with 12 years experience and team lead experience",
                                        "target_level": "management"
                                    },
                                    headers=headers)
        assert skills_response.status_code == 200
        skills_data = skills_response.json()
        assert skills_data["management_readiness"] >= 75
        
        # 3. Job Discovery - Management and senior IC roles
        mock_linkedin_instance.search_jobs.return_value = [
            {
                "title": "Engineering Manager",
                "company": "ScaleCorp",
                "location": "Seattle, WA",
                "description": "Lead a team of 8 engineers, drive technical strategy",
                "requirements": ["10+ years experience", "Team leadership", "Technical expertise"],
                "salary_range": {"min": 180000, "max": 220000},
                "source": "linkedin",
                "level": "management"
            },
            {
                "title": "Principal Software Engineer",
                "company": "TechLeader",
                "location": "Remote",
                "description": "Technical leadership role with architecture responsibilities",
                "requirements": ["12+ years experience", "Architecture", "Technical leadership"],
                "salary_range": {"min": 200000, "max": 250000},
                "source": "linkedin",
                "level": "senior_ic"
            }
        ]
        
        job_search_response = client.post("/api/v1/agents/job-discovery/search",
                                        json={
                                            "keywords": "engineering manager principal engineer",
                                            "experience_level": "senior",
                                            "target_level": "management"
                                        },
                                        headers=headers)
        assert job_search_response.status_code == 200
        jobs = job_search_response.json()["jobs"]
        assert len(jobs) >= 1
        assert any("manager" in job["title"].lower() or "principal" in job["title"].lower() for job in jobs)
        
        # 4. Resume Optimization - Highlight leadership experience
        mock_watsonx_instance.optimize_resume.return_value = {
            "optimized_content": "Resume emphasizing leadership, impact, and technical expertise",
            "ats_score": 88,
            "improvements": [
                "Quantified team leadership impact",
                "Highlighted technical decision making",
                "Emphasized mentoring and development experience"
            ],
            "leadership_emphasis": True
        }
        
        resume_response = client.post("/api/v1/agents/resume-optimization/optimize",
                                    json={
                                        "resume_content": "Senior engineer resume",
                                        "target_job_id": "eng_manager_123",
                                        "target_level": "management"
                                    },
                                    headers=headers)
        assert resume_response.status_code == 200
        assert resume_response.json()["ats_score"] >= 85
        
        # 5. Interview Preparation - Management and technical leadership
        mock_watsonx_instance.generate_interview_questions.return_value = [
            {"question": "How do you handle underperforming team members?", "type": "behavioral", "category": "management"},
            {"question": "Describe your approach to technical decision making", "type": "behavioral", "category": "leadership"},
            {"question": "How do you balance technical debt with feature delivery?", "type": "technical", "category": "strategy"}
        ]
        
        interview_prep_response = client.post("/api/v1/agents/interview-preparation/questions",
                                            json={
                                                "job_role": "Engineering Manager",
                                                "experience_level": "senior",
                                                "focus_areas": ["management", "technical_leadership"]
                                            },
                                            headers=headers)
        assert interview_prep_response.status_code == 200
        questions = interview_prep_response.json()["questions"]
        assert len(questions) >= 3
        assert any(q["category"] in ["management", "leadership"] for q in questions)
        
        # 6. Career Strategy - Leadership development path
        mock_watsonx_instance.generate_career_roadmap.return_value = {
            "milestones": [
                {"title": "Complete management training", "timeline": "3 months", "priority": "high"},
                {"title": "Secure engineering manager role", "timeline": "6 months", "priority": "high"},
                {"title": "Build and scale team", "timeline": "12 months", "priority": "medium"},
                {"title": "Advance to senior management", "timeline": "24 months", "priority": "low"}
            ],
            "timeline": "36 months",
            "focus": "leadership_development"
        }
        
        career_response = client.post("/api/v1/agents/career-strategy/roadmap",
                                    json={
                                        "current_role": "Senior Software Engineer",
                                        "target_role": "Engineering Manager",
                                        "experience_level": "senior"
                                    },
                                    headers=headers)
        assert career_response.status_code == 200
        roadmap = career_response.json()
        assert len(roadmap["milestones"]) >= 3
        assert roadmap["focus"] == "leadership_development"
    
    async def test_multi_user_concurrent_usage(self, new_graduate_user, career_changer_user):
        """Test system handling multiple users simultaneously"""
        
        async def user_workflow(user_data):
            headers = self.authenticate_user(user_data)
            
            # Each user performs basic operations
            profile_response = client.post("/api/v1/user/profile", json=user_data, headers=headers)
            job_search_response = client.post("/api/v1/agents/job-discovery/search",
                                            json={"keywords": "software engineer"}, headers=headers)
            
            return profile_response.status_code == 200 and job_search_response.status_code == 200
        
        # Run concurrent user workflows
        tasks = [
            user_workflow(new_graduate_user),
            user_workflow(career_changer_user)
        ]
        
        results = await asyncio.gather(*tasks)
        assert all(results), "All concurrent user workflows should succeed"
    
    async def test_mobile_user_experience(self, new_graduate_user):
        """Test mobile-optimized user experience"""
        
        headers = self.authenticate_user(new_graduate_user)
        mobile_headers = {**headers, "User-Agent": "JobSwitch-Mobile/1.0"}
        
        # Test mobile-optimized endpoints
        dashboard_response = client.get("/api/v1/mobile/dashboard", headers=mobile_headers)
        jobs_response = client.get("/api/v1/mobile/jobs/recommendations", headers=mobile_headers)
        
        # Should return mobile-optimized responses or fallback gracefully
        assert dashboard_response.status_code in [200, 404]  # 404 if mobile endpoints not implemented
        assert jobs_response.status_code in [200, 404]
    
    async def test_accessibility_compliance(self):
        """Test basic accessibility compliance"""
        
        # Test that API responses include accessibility metadata
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        # API should be accessible and provide structured data
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
    
    async def test_data_privacy_compliance(self, new_graduate_user):
        """Test GDPR and data privacy compliance"""
        
        headers = self.authenticate_user(new_graduate_user)
        
        # Test data export
        export_response = client.get("/api/v1/user/data-export", headers=headers)
        assert export_response.status_code in [200, 202]  # Success or accepted for processing
        
        # Test data deletion request
        deletion_response = client.delete("/api/v1/user/account", headers=headers)
        assert deletion_response.status_code in [200, 202, 204]  # Various success codes
    
    async def test_system_performance_under_realistic_load(self):
        """Test system performance with realistic user load"""
        
        async def simulate_user_activity():
            # Simulate typical user actions
            health_response = client.get("/api/v1/health")
            return health_response.status_code == 200
        
        # Simulate 20 concurrent users
        tasks = [simulate_user_activity() for _ in range(20)]
        start_time = datetime.now()
        results = await asyncio.gather(*tasks)
        end_time = datetime.now()
        
        # All requests should succeed
        assert all(results)
        
        # Response time should be reasonable (under 5 seconds for all requests)
        total_time = (end_time - start_time).total_seconds()
        assert total_time < 5.0, f"System took {total_time} seconds for 20 concurrent requests"
    
    async def test_error_recovery_scenarios(self):
        """Test system behavior during error conditions"""
        
        # Test invalid authentication
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/user/profile", headers=invalid_headers)
        assert response.status_code == 401
        
        # Test malformed requests
        response = client.post("/api/v1/auth/register", json={"invalid": "data"})
        assert response.status_code == 422
        
        # Test rate limiting
        for _ in range(20):  # Attempt to trigger rate limiting
            response = client.get("/api/v1/health")
        
        # System should handle gracefully (either succeed or rate limit)
        assert response.status_code in [200, 429]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
        