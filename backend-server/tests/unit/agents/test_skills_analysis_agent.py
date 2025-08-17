"""
Unit tests for Skills Analysis Agent
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.agents.skills_analysis import SkillsAnalysisAgent


class TestSkillsAnalysisAgent:
    """Test cases for SkillsAnalysisAgent class"""
    
    @pytest.fixture
    def skills_agent(self, mock_watsonx_client, mock_langchain_manager):
        """Create a SkillsAnalysisAgent instance for testing"""
        return SkillsAnalysisAgent(mock_watsonx_client, mock_langchain_manager)
    
    def test_agent_initialization(self, skills_agent):
        """Test skills analysis agent initialization"""
        assert skills_agent.agent_id is not None
        assert skills_agent.agent_type == "skills_analysis"
        assert skills_agent.watsonx is not None
        assert skills_agent.langchain is not None
    
    @pytest.mark.asyncio
    async def test_extract_skills_from_resume(self, skills_agent, sample_user_profile, mock_database):
        """Test skill extraction from resume"""
        resume_text = """
        John Doe - Senior Software Engineer
        
        Experience:
        • 5+ years developing web applications using React, Node.js, and Python
        • Proficient in AWS cloud services including EC2, S3, and Lambda
        • Experience with Docker containerization and Kubernetes orchestration
        • Strong background in database design with PostgreSQL and MongoDB
        """
        
        task_data = {
            "task_type": "extract_skills_from_resume",
            "user_id": "user-123",
            "resume_text": resume_text
        }
        
        with patch('app.core.database.get_database', return_value=mock_database):
            result = await skills_agent._extract_skills_from_resume(
                sample_user_profile,
                task_data,
                mock_database
            )
            
            assert result["success"] is True
            assert "skills_extracted" in result["data"]
            assert "total_skills_extracted" in result["data"]
    
    @pytest.mark.asyncio
    async def test_analyze_skill_gaps(self, skills_agent, sample_user_profile, mock_database):
        """Test skill gap analysis"""
        job_description = """
        We are looking for a Senior DevOps Engineer with:
        - 5+ years experience with Kubernetes
        - Strong Python and Go programming skills
        - Experience with CI/CD pipelines
        - AWS cloud expertise
        - Docker containerization experience
        """
        
        task_data = {
            "task_type": "analyze_skill_gaps",
            "user_id": "user-123",
            "job_description": job_description,
            "job_title": "Senior DevOps Engineer"
        }
        
        with patch('app.core.database.get_database', return_value=mock_database):
            result = await skills_agent._analyze_skill_gaps(
                sample_user_profile,
                task_data,
                mock_database
            )
            
            assert result["success"] is True
            assert "matching_skills" in result["data"]
            assert "critical_gaps" in result["data"]
            assert "overall_readiness" in result["data"]
    
    @pytest.mark.asyncio
    async def test_recommend_learning_paths(self, skills_agent, sample_user_profile, mock_database):
        """Test learning path recommendations"""
        task_data = {
            "task_type": "recommend_learning_paths",
            "user_id": "user-123",
            "target_skills": ["Kubernetes", "Docker", "CI/CD"],
            "timeline": "6 months"
        }
        
        with patch('app.core.database.get_database', return_value=mock_database):
            result = await skills_agent._recommend_learning_paths(
                sample_user_profile,
                task_data,
                mock_database
            )
            
            assert result["success"] is True
            assert "learning_paths" in result["data"]
            assert "overall_timeline" in result["data"]
            assert "budget_estimate" in result["data"]
    
    @pytest.mark.asyncio
    async def test_analyze_user_skills(self, skills_agent, sample_user_profile, mock_database):
        """Test comprehensive user skills analysis"""
        task_data = {
            "task_type": "analyze_skills",
            "user_id": "user-123"
        }
        
        with patch('app.core.database.get_database', return_value=mock_database):
            result = await skills_agent._analyze_user_skills(
                sample_user_profile,
                task_data,
                mock_database
            )
            
            assert result["success"] is True
            assert "skill_distribution" in result["data"]
            assert "strengths" in result["data"]
            assert "improvement_areas" in result["data"]
            assert "market_analysis" in result["data"]
    
    @pytest.mark.asyncio
    async def test_skill_categorization(self, skills_agent):
        """Test skill categorization functionality"""
        skills = [
            "Python", "React", "Leadership", "AWS", "Communication",
            "Docker", "Project Management", "PostgreSQL"
        ]
        
        categorized = await skills_agent._categorize_skills(skills)
        
        assert "technical" in categorized
        assert "soft" in categorized
        assert "domain" in categorized
        assert len(categorized["technical"]) > 0
        assert len(categorized["soft"]) > 0
    
    @pytest.mark.asyncio
    async def test_skill_proficiency_assessment(self, skills_agent, sample_user_profile):
        """Test skill proficiency assessment"""
        skill_name = "Python"
        experience_data = sample_user_profile["experience"]
        
        proficiency = await skills_agent._assess_skill_proficiency(
            skill_name,
            experience_data
        )
        
        assert proficiency in ["beginner", "intermediate", "advanced", "expert"]
    
    @pytest.mark.asyncio
    async def test_market_demand_analysis(self, skills_agent):
        """Test market demand analysis for skills"""
        skills = ["Python", "React", "Kubernetes", "COBOL"]
        
        with patch('app.integrations.job_connectors.JobConnectors') as mock_connectors:
            mock_connector_instance = Mock()
            mock_connector_instance.analyze_skill_demand = AsyncMock(return_value={
                "Python": {"demand": "high", "growth": "stable"},
                "React": {"demand": "high", "growth": "growing"},
                "Kubernetes": {"demand": "medium", "growth": "growing"},
                "COBOL": {"demand": "low", "growth": "declining"}
            })
            mock_connectors.return_value = mock_connector_instance
            
            demand_analysis = await skills_agent._analyze_market_demand(skills)
            
            assert "Python" in demand_analysis
            assert demand_analysis["Python"]["demand"] == "high"
    
    @pytest.mark.asyncio
    async def test_learning_resource_recommendations(self, skills_agent):
        """Test learning resource recommendations"""
        skill = "Kubernetes"
        current_level = "beginner"
        target_level = "intermediate"
        
        resources = await skills_agent._recommend_learning_resources(
            skill,
            current_level,
            target_level
        )
        
        assert "courses" in resources
        assert "books" in resources
        assert "certifications" in resources
        assert "projects" in resources
    
    @pytest.mark.asyncio
    async def test_skill_gap_prioritization(self, skills_agent):
        """Test skill gap prioritization"""
        gaps = [
            {"skill": "Kubernetes", "importance": "high", "difficulty": "medium"},
            {"skill": "Docker", "importance": "medium", "difficulty": "low"},
            {"skill": "Go", "importance": "low", "difficulty": "high"}
        ]
        
        prioritized = await skills_agent._prioritize_skill_gaps(gaps)
        
        assert len(prioritized) == len(gaps)
        # Should be sorted by priority (importance vs difficulty)
        assert prioritized[0]["priority_score"] >= prioritized[-1]["priority_score"]
    
    @pytest.mark.asyncio
    async def test_process_request_extract_skills(self, skills_agent):
        """Test process_request for skill extraction"""
        request_data = {
            "task_type": "extract_skills_from_resume",
            "user_id": "user-123",
            "resume_text": "Python developer with 5 years experience"
        }
        
        with patch.object(skills_agent, '_extract_skills_from_resume') as mock_extract:
            mock_extract.return_value = {
                "success": True,
                "data": {"skills_extracted": ["Python"], "total_skills_extracted": 1}
            }
            
            result = await skills_agent.process_request(request_data, {})
            
            assert result["success"] is True
            mock_extract.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_request_analyze_gaps(self, skills_agent):
        """Test process_request for gap analysis"""
        request_data = {
            "task_type": "analyze_skill_gaps",
            "user_id": "user-123",
            "job_description": "Looking for Python developer with AWS experience"
        }
        
        with patch.object(skills_agent, '_analyze_skill_gaps') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "data": {"critical_gaps": [], "matching_skills": []}
            }
            
            result = await skills_agent.process_request(request_data, {})
            
            assert result["success"] is True
            mock_analyze.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recommendations(self, skills_agent, sample_user_profile):
        """Test get_recommendations method"""
        with patch.object(skills_agent, '_analyze_user_skills') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "data": {
                    "improvement_areas": [
                        {
                            "category": "DevOps",
                            "skills": ["Kubernetes", "Docker"],
                            "priority": "high"
                        }
                    ],
                    "market_analysis": {
                        "high_demand_skills": ["Python", "React"]
                    }
                }
            }
            
            recommendations = await skills_agent.get_recommendations(sample_user_profile)
            
            assert len(recommendations) > 0
            assert "title" in recommendations[0]
            assert "priority" in recommendations[0]
    
    @pytest.mark.asyncio
    async def test_skill_validation(self, skills_agent):
        """Test skill validation and normalization"""
        raw_skills = [
            "python", "REACT", "node.js", "Node JS", "aws", "Amazon Web Services"
        ]
        
        validated_skills = await skills_agent._validate_and_normalize_skills(raw_skills)
        
        assert "Python" in validated_skills
        assert "React" in validated_skills
        assert "Node.js" in validated_skills
        assert "AWS" in validated_skills
        # Should deduplicate similar skills
        assert len(validated_skills) <= len(raw_skills)
    
    @pytest.mark.asyncio
    async def test_skill_trend_analysis(self, skills_agent):
        """Test skill trend analysis"""
        skills = ["Python", "React", "Vue.js", "Angular"]
        
        trends = await skills_agent._analyze_skill_trends(skills)
        
        assert isinstance(trends, dict)
        for skill in skills:
            if skill in trends:
                assert "trend" in trends[skill]
                assert "growth_rate" in trends[skill]
    
    @pytest.mark.asyncio
    async def test_certification_recommendations(self, skills_agent, sample_user_profile):
        """Test certification recommendations"""
        target_role = "Cloud Architect"
        
        certifications = await skills_agent._recommend_certifications(
            sample_user_profile,
            target_role
        )
        
        assert "certifications" in certifications
        assert len(certifications["certifications"]) > 0
        
        for cert in certifications["certifications"]:
            assert "name" in cert
            assert "provider" in cert
            assert "difficulty" in cert
            assert "relevance_score" in cert
    
    @pytest.mark.asyncio
    async def test_error_handling(self, skills_agent):
        """Test error handling in skills analysis"""
        request_data = {
            "task_type": "invalid_task",
            "user_id": "user-123"
        }
        
        result = await skills_agent.process_request(request_data, {})
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_skill_progress_tracking(self, skills_agent, mock_database):
        """Test skill progress tracking"""
        progress_data = {
            "user_id": "user-123",
            "skill": "Kubernetes",
            "previous_level": "beginner",
            "current_level": "intermediate",
            "progress_date": datetime.utcnow().isoformat()
        }
        
        with patch('app.core.database.get_database', return_value=mock_database):
            result = await skills_agent._track_skill_progress(progress_data)
            
            assert result["success"] is True
            mock_database.add.assert_called_once()
            mock_database.commit.assert_called_once()