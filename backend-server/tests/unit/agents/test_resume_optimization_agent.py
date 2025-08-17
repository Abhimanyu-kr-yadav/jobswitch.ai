"""
Unit tests for Resume Optimization Agent
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.agents.resume_optimization import ResumeOptimizationAgent


class TestResumeOptimizationAgent:
    """Test cases for ResumeOptimizationAgent class"""
    
    @pytest.fixture
    def resume_agent(self, mock_watsonx_client, mock_langchain_manager):
        """Create a ResumeOptimizationAgent instance for testing"""
        return ResumeOptimizationAgent(mock_watsonx_client, mock_langchain_manager)
    
    def test_agent_initialization(self, resume_agent):
        """Test resume optimization agent initialization"""
        assert resume_agent.agent_id is not None
        assert resume_agent.agent_type == "resume_optimization"
        assert resume_agent.watsonx is not None
        assert resume_agent.langchain is not None
    
    @pytest.mark.asyncio
    async def test_optimize_resume_for_job(self, resume_agent, sample_resume, sample_job_posting, mock_database):
        """Test resume optimization for specific job"""
        task_data = {
            "task_type": "optimize_resume",
            "user_id": "user-123",
            "resume_id": "resume-123",
            "job_id": "job-123"
        }
        
        with patch('app.core.database.get_database', return_value=mock_database):
            # Mock resume and job retrieval
            mock_resume = Mock()
            mock_resume.to_dict.return_value = sample_resume
            mock_job = Mock()
            mock_job.to_dict.return_value = sample_job_posting
            
            mock_database.query.return_value.filter.return_value.first.side_effect = [mock_resume, mock_job]
            
            result = await resume_agent._optimize_resume_for_job(
                sample_resume,
                task_data,
                mock_database
            )
            
            assert result["success"] is True
            assert "optimized_resume" in result["data"]
            assert "ats_score" in result["data"]
            assert "improvements" in result["data"]
    
    @pytest.mark.asyncio
    async def test_calculate_ats_score(self, resume_agent, sample_resume, sample_job_posting):
        """Test ATS compatibility score calculation"""
        score_data = await resume_agent._calculate_ats_score(
            sample_resume["content"],
            sample_job_posting
        )
        
        assert isinstance(score_data, dict)
        assert "overall_score" in score_data
        assert "keyword_match" in score_data
        assert "format_score" in score_data
        assert "readability_score" in score_data
        assert 0 <= score_data["overall_score"] <= 100
    
    @pytest.mark.asyncio
    async def test_extract_keywords_from_job(self, resume_agent, sample_job_posting):
        """Test keyword extraction from job posting"""
        keywords = await resume_agent._extract_keywords_from_job(sample_job_posting)
        
        assert isinstance(keywords, dict)
        assert "technical_keywords" in keywords
        assert "soft_skills" in keywords
        assert "required_keywords" in keywords
        assert "nice_to_have_keywords" in keywords
    
    @pytest.mark.asyncio
    async def test_generate_resume_content(self, resume_agent, sample_resume, sample_job_posting):
        """Test resume content generation"""
        optimization_data = {
            "target_keywords": ["Python", "React", "AWS"],
            "job_requirements": sample_job_posting["requirements"],
            "current_content": sample_resume["content"]
        }
        
        generated_content = await resume_agent._generate_resume_content(optimization_data)
        
        assert isinstance(generated_content, dict)
        assert "personal_info" in generated_content
        assert "summary" in generated_content
        assert "experience" in generated_content
        assert "skills" in generated_content
    
    @pytest.mark.asyncio
    async def test_create_resume_version(self, resume_agent, sample_resume, mock_database):
        """Test creating new resume version"""
        version_data = {
            "user_id": "user-123",
            "base_resume_id": "resume-123",
            "target_job_id": "job-123",
            "optimized_content": {"summary": "Updated summary"},
            "ats_score": 85
        }
        
        with patch('app.core.database.get_database', return_value=mock_database):
            result = await resume_agent._create_resume_version(version_data)
            
            assert result["success"] is True
            assert "resume_id" in result["data"]
            mock_database.add.assert_called_once()
            mock_database.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_compare_resume_versions(self, resume_agent, mock_database):
        """Test resume version comparison"""
        version1_id = "resume-123-v1"
        version2_id = "resume-123-v2"
        
        # Mock resume versions
        mock_resume1 = Mock()
        mock_resume1.to_dict.return_value = {
            "resume_id": version1_id,
            "content": {"summary": "Original summary"},
            "ats_score": 70
        }
        mock_resume2 = Mock()
        mock_resume2.to_dict.return_value = {
            "resume_id": version2_id,
            "content": {"summary": "Optimized summary"},
            "ats_score": 85
        }
        
        mock_database.query.return_value.filter.return_value.first.side_effect = [mock_resume1, mock_resume2]
        
        with patch('app.core.database.get_database', return_value=mock_database):
            comparison = await resume_agent._compare_resume_versions(version1_id, version2_id)
            
            assert comparison["success"] is True
            assert "comparison" in comparison["data"]
            assert "score_improvement" in comparison["data"]["comparison"]
    
    @pytest.mark.asyncio
    async def test_analyze_resume_format(self, resume_agent, sample_resume):
        """Test resume format analysis"""
        format_analysis = await resume_agent._analyze_resume_format(sample_resume["content"])
        
        assert isinstance(format_analysis, dict)
        assert "format_score" in format_analysis
        assert "issues" in format_analysis
        assert "recommendations" in format_analysis
    
    @pytest.mark.asyncio
    async def test_optimize_resume_sections(self, resume_agent, sample_resume, sample_job_posting):
        """Test individual resume section optimization"""
        sections = ["summary", "experience", "skills"]
        
        for section in sections:
            optimized_section = await resume_agent._optimize_resume_section(
                section,
                sample_resume["content"].get(section),
                sample_job_posting
            )
            
            assert optimized_section is not None
            assert isinstance(optimized_section, (str, list, dict))
    
    @pytest.mark.asyncio
    async def test_calculate_acceptance_probability(self, resume_agent, sample_resume, sample_job_posting):
        """Test acceptance probability calculation"""
        probability = await resume_agent._calculate_acceptance_probability(
            sample_resume,
            sample_job_posting
        )
        
        assert isinstance(probability, dict)
        assert "probability_score" in probability
        assert "confidence_level" in probability
        assert "factors" in probability
        assert 0 <= probability["probability_score"] <= 1
    
    @pytest.mark.asyncio
    async def test_generate_cover_letter(self, resume_agent, sample_resume, sample_job_posting):
        """Test cover letter generation"""
        cover_letter_data = {
            "user_profile": sample_resume,
            "job_posting": sample_job_posting,
            "tone": "professional",
            "length": "medium"
        }
        
        cover_letter = await resume_agent._generate_cover_letter(cover_letter_data)
        
        assert isinstance(cover_letter, dict)
        assert "content" in cover_letter
        assert "subject_line" in cover_letter
        assert len(cover_letter["content"]) > 100  # Should be substantial content
    
    @pytest.mark.asyncio
    async def test_process_request_optimize_resume(self, resume_agent):
        """Test process_request for resume optimization"""
        request_data = {
            "task_type": "optimize_resume",
            "user_id": "user-123",
            "resume_id": "resume-123",
            "job_id": "job-123"
        }
        
        with patch.object(resume_agent, '_optimize_resume_for_job') as mock_optimize:
            mock_optimize.return_value = {
                "success": True,
                "data": {"optimized_resume": {}, "ats_score": 85}
            }
            
            result = await resume_agent.process_request(request_data, {})
            
            assert result["success"] is True
            mock_optimize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_request_calculate_ats_score(self, resume_agent):
        """Test process_request for ATS score calculation"""
        request_data = {
            "task_type": "calculate_ats_score",
            "user_id": "user-123",
            "resume_id": "resume-123",
            "job_id": "job-123"
        }
        
        with patch.object(resume_agent, '_calculate_ats_score') as mock_calculate:
            mock_calculate.return_value = {
                "overall_score": 85,
                "keyword_match": 80,
                "format_score": 90
            }
            
            result = await resume_agent.process_request(request_data, {})
            
            assert result["success"] is True
            mock_calculate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recommendations(self, resume_agent, sample_user_profile):
        """Test get_recommendations method"""
        with patch.object(resume_agent, '_analyze_user_resumes') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "data": {
                    "resume_recommendations": [
                        {
                            "title": "Optimize resume for Software Engineer role",
                            "priority": "high",
                            "description": "Improve ATS score by adding relevant keywords"
                        }
                    ]
                }
            }
            
            recommendations = await resume_agent.get_recommendations(sample_user_profile)
            
            assert len(recommendations) > 0
            assert "title" in recommendations[0]
            assert "priority" in recommendations[0]
    
    @pytest.mark.asyncio
    async def test_resume_parsing(self, resume_agent):
        """Test resume parsing from different formats"""
        # Test text resume parsing
        text_resume = """
        John Doe
        Software Engineer
        john.doe@email.com
        
        Experience:
        Software Engineer at TechCorp (2020-2023)
        - Developed web applications using Python and React
        - Improved system performance by 30%
        
        Skills: Python, React, AWS, PostgreSQL
        """
        
        parsed_resume = await resume_agent._parse_resume_text(text_resume)
        
        assert isinstance(parsed_resume, dict)
        assert "personal_info" in parsed_resume
        assert "experience" in parsed_resume
        assert "skills" in parsed_resume
    
    @pytest.mark.asyncio
    async def test_keyword_optimization(self, resume_agent):
        """Test keyword optimization in resume content"""
        content = "Developed web applications using Python"
        target_keywords = ["Python", "Django", "REST API", "PostgreSQL"]
        
        optimized_content = await resume_agent._optimize_keywords(content, target_keywords)
        
        assert isinstance(optimized_content, str)
        assert len(optimized_content) >= len(content)
        # Should include more target keywords
    
    @pytest.mark.asyncio
    async def test_resume_template_selection(self, resume_agent, sample_job_posting):
        """Test resume template selection based on job"""
        template = await resume_agent._select_resume_template(sample_job_posting)
        
        assert isinstance(template, dict)
        assert "template_name" in template
        assert "sections" in template
        assert "formatting" in template
    
    @pytest.mark.asyncio
    async def test_error_handling(self, resume_agent):
        """Test error handling in resume optimization"""
        request_data = {
            "task_type": "invalid_task",
            "user_id": "user-123"
        }
        
        result = await resume_agent.process_request(request_data, {})
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_resume_metrics_tracking(self, resume_agent, mock_database):
        """Test resume performance metrics tracking"""
        metrics_data = {
            "resume_id": "resume-123",
            "job_applications": 10,
            "interview_invitations": 3,
            "response_rate": 0.3,
            "tracking_period": "30_days"
        }
        
        with patch('app.core.database.get_database', return_value=mock_database):
            result = await resume_agent._track_resume_metrics(metrics_data)
            
            assert result["success"] is True
            mock_database.add.assert_called_once()
            mock_database.commit.assert_called_once()