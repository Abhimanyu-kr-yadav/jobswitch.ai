"""
Test Skills Analysis Agent Implementation
"""
import asyncio
import json
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.agents.skills_analysis import SkillsAnalysisAgent
from app.integrations.watsonx import WatsonXClient
from app.integrations.langchain_utils import LangChainAgentManager
from app.models.user import UserProfile
from app.core.database import get_database
from datetime import datetime


class MockWatsonXClient:
    """Mock WatsonX client for testing"""
    
    async def generate_text(self, prompt, model_id="mock-model"):
        """Mock text generation"""
        if "extract" in prompt.lower() and "skills" in prompt.lower():
            # Mock skill extraction response
            return {
                "success": True,
                "generated_text": json.dumps({
                    "technical_skills": [
                        {"name": "Python", "category": "programming", "proficiency": "advanced", "years_experience": 5},
                        {"name": "React", "category": "frontend", "proficiency": "intermediate", "years_experience": 3},
                        {"name": "AWS", "category": "cloud", "proficiency": "intermediate", "years_experience": 2}
                    ],
                    "soft_skills": [
                        {"name": "Leadership", "category": "management", "proficiency": "advanced"},
                        {"name": "Communication", "category": "interpersonal", "proficiency": "expert"}
                    ],
                    "certifications": [
                        {"name": "AWS Solutions Architect", "issuer": "Amazon", "year": 2023}
                    ],
                    "domain_expertise": [
                        {"name": "Web Development", "years_experience": 5}
                    ]
                })
            }
        elif "gap analysis" in prompt.lower() or "compatibility" in prompt.lower():
            # Mock gap analysis response
            return {
                "success": True,
                "generated_text": json.dumps({
                    "matching_skills": [
                        {"name": "Python", "user_proficiency": "advanced", "required_level": "intermediate", "match_strength": "strong"}
                    ],
                    "critical_gaps": [
                        {"name": "Kubernetes", "required_level": "intermediate", "priority": "high", "estimated_learning_time": "3-6 months"}
                    ],
                    "nice_to_have_gaps": [
                        {"name": "GraphQL", "required_level": "basic", "priority": "low", "estimated_learning_time": "1-2 months"}
                    ],
                    "transferable_skills": [
                        {"user_skill": "Docker", "applicable_to": "Container Orchestration", "relevance": "high"}
                    ],
                    "overall_readiness": {
                        "percentage": 75,
                        "readiness_level": "good",
                        "key_strengths": ["Strong programming background", "Cloud experience"],
                        "main_concerns": ["Limited DevOps experience", "No Kubernetes knowledge"]
                    },
                    "development_priority": [
                        {"skill": "Kubernetes", "priority": 1, "reason": "Critical for role success"}
                    ]
                })
            }
        elif "learning path" in prompt.lower():
            # Mock learning path response
            return {
                "success": True,
                "generated_text": json.dumps({
                    "learning_paths": [
                        {
                            "skill": "Kubernetes",
                            "current_level": "beginner",
                            "target_level": "intermediate",
                            "estimated_duration": "3-6 months",
                            "prerequisites": ["Docker", "Linux"],
                            "learning_steps": [
                                {
                                    "step": 1,
                                    "title": "Kubernetes Fundamentals",
                                    "duration": "4-6 weeks",
                                    "resources": [
                                        {"type": "course", "name": "Kubernetes Basics", "provider": "Coursera"}
                                    ]
                                }
                            ],
                            "projects": [
                                {"name": "Deploy Sample App", "difficulty": "beginner", "estimated_time": "1 week"}
                            ],
                            "certifications": [
                                {"name": "CKA", "provider": "CNCF", "difficulty": "intermediate"}
                            ]
                        }
                    ],
                    "overall_timeline": "6-12 months",
                    "priority_order": ["Kubernetes", "Docker", "CI/CD"],
                    "budget_estimate": {
                        "free_resources": 60,
                        "paid_courses": 500,
                        "certifications": 300,
                        "total_estimated": 800
                    }
                })
            }
        elif "analyze" in prompt.lower() and "skills" in prompt.lower():
            # Mock skills analysis response
            return {
                "success": True,
                "generated_text": json.dumps({
                    "skill_distribution": {
                        "technical": 70,
                        "soft": 20,
                        "domain": 10
                    },
                    "strengths": [
                        {"category": "Programming", "skills": ["Python", "JavaScript"], "market_demand": "high"}
                    ],
                    "improvement_areas": [
                        {"category": "DevOps", "current_level": "basic", "importance": "high", "reason": "Career advancement"}
                    ],
                    "market_analysis": {
                        "high_demand_skills": ["Kubernetes", "React", "Python"],
                        "emerging_skills": ["AI/ML", "Blockchain"],
                        "declining_skills": ["jQuery", "Flash"]
                    },
                    "career_opportunities": [
                        {"role": "Senior Developer", "match_percentage": 85, "missing_skills": ["Leadership"]}
                    ]
                })
            }
        
        return {
            "success": True,
            "generated_text": "Mock response for: " + prompt[:100] + "..."
        }


class MockLangChainManager:
    """Mock LangChain manager for testing"""
    
    def __init__(self):
        self.available = True
    
    async def process_with_chain(self, chain, input_data):
        return {
            "success": True,
            "result": "Mock LangChain result",
            "processing_time_ms": 100
        }


async def test_skills_analysis_agent():
    """Test the Skills Analysis Agent functionality"""
    
    print("🧪 Testing Skills Analysis Agent...")
    
    # Initialize mock clients
    mock_watsonx = MockWatsonXClient()
    mock_langchain = MockLangChainManager()
    
    # Initialize agent
    agent = SkillsAnalysisAgent(mock_watsonx, mock_langchain)
    
    print(f"✅ Agent initialized: {agent.agent_id}")
    
    # Test 1: Extract skills from resume
    print("\n📝 Test 1: Extract skills from resume")
    
    resume_text = """
    John Doe
    Senior Software Engineer
    
    Experience:
    • 5+ years developing web applications using React, Node.js, and Python
    • Proficient in AWS cloud services including EC2, S3, and Lambda
    • Experience with Docker containerization and Kubernetes orchestration
    • Strong background in database design with PostgreSQL and MongoDB
    • Led team of 4 developers in agile development environment
    • Excellent communication and problem-solving skills
    
    Certifications:
    • AWS Certified Solutions Architect (2023)
    • Certified Kubernetes Administrator (2022)
    """
    
    task_data = {
        "task_type": "extract_skills_from_resume",
        "user_id": "test_user_123",
        "resume_text": resume_text
    }
    
    try:
        # Create a mock user profile for testing
        mock_user_profile = type('MockUserProfile', (), {
            'user_id': 'test_user_123',
            'skills': [],
            'certifications': [],
            'updated_at': datetime.utcnow(),
            'to_dict': lambda: {'user_id': 'test_user_123', 'skills': []}
        })()
        
        # Mock database session
        class MockDB:
            def query(self, model):
                return self
            
            def filter(self, condition):
                return self
            
            def first(self):
                return mock_user_profile
            
            def add(self, obj):
                pass
            
            def commit(self):
                pass
        
        # Patch the get_database function temporarily
        original_get_database = None
        try:
            from app.core.database import get_database
            original_get_database = get_database
        except:
            pass
        
        # Override the process_task method to avoid database dependency
        async def mock_process_task(task_data):
            if task_data["task_type"] == "extract_skills_from_resume":
                return await agent._extract_skills_from_resume(mock_user_profile, task_data, MockDB())
            elif task_data["task_type"] == "analyze_skill_gaps":
                return await agent._analyze_skill_gaps(mock_user_profile, task_data, MockDB())
            elif task_data["task_type"] == "recommend_learning_paths":
                return await agent._recommend_learning_paths(mock_user_profile, task_data, MockDB())
            elif task_data["task_type"] == "analyze_skills":
                return await agent._analyze_user_skills(mock_user_profile, task_data, MockDB())
        
        # Test skill extraction
        result = await mock_process_task(task_data)
        
        if result["success"]:
            print("✅ Skills extraction successful")
            print(f"   - Skills extracted: {result['data']['total_skills_extracted']}")
            print(f"   - Certifications found: {len(result['data'].get('certifications', []))}")
        else:
            print(f"❌ Skills extraction failed: {result.get('error')}")
        
    except Exception as e:
        print(f"❌ Skills extraction test failed: {str(e)}")
    
    # Test 2: Analyze skill gaps
    print("\n🔍 Test 2: Analyze skill gaps")
    
    gap_task_data = {
        "task_type": "analyze_skill_gaps",
        "user_id": "test_user_123",
        "job_description": """
        We are looking for a Senior DevOps Engineer with:
        - 5+ years experience with Kubernetes
        - Strong Python and Go programming skills
        - Experience with CI/CD pipelines
        - AWS cloud expertise
        - Docker containerization experience
        """,
        "job_title": "Senior DevOps Engineer"
    }
    
    try:
        result = await mock_process_task(gap_task_data)
        
        if result["success"]:
            print("✅ Gap analysis successful")
            readiness = result['data'].get('overall_readiness', {})
            print(f"   - Overall readiness: {readiness.get('percentage', 0)}%")
            print(f"   - Critical gaps: {len(result['data'].get('critical_gaps', []))}")
            print(f"   - Matching skills: {len(result['data'].get('matching_skills', []))}")
        else:
            print(f"❌ Gap analysis failed: {result.get('error')}")
        
    except Exception as e:
        print(f"❌ Gap analysis test failed: {str(e)}")
    
    # Test 3: Generate learning paths
    print("\n📚 Test 3: Generate learning paths")
    
    learning_task_data = {
        "task_type": "recommend_learning_paths",
        "user_id": "test_user_123",
        "target_skills": ["Kubernetes", "Docker", "CI/CD"]
    }
    
    try:
        result = await mock_process_task(learning_task_data)
        
        if result["success"]:
            print("✅ Learning path generation successful")
            paths = result['data'].get('learning_paths', [])
            print(f"   - Learning paths generated: {len(paths)}")
            print(f"   - Overall timeline: {result['data'].get('overall_timeline', 'N/A')}")
            print(f"   - Estimated budget: ${result['data'].get('budget_estimate', {}).get('total_estimated', 0)}")
        else:
            print(f"❌ Learning path generation failed: {result.get('error')}")
        
    except Exception as e:
        print(f"❌ Learning path generation test failed: {str(e)}")
    
    # Test 4: Analyze user skills
    print("\n📊 Test 4: Analyze user skills")
    
    analysis_task_data = {
        "task_type": "analyze_skills",
        "user_id": "test_user_123"
    }
    
    try:
        result = await mock_process_task(analysis_task_data)
        
        if result["success"]:
            print("✅ Skills analysis successful")
            distribution = result['data'].get('skill_distribution', {})
            print(f"   - Technical skills: {distribution.get('technical', 0)}%")
            print(f"   - Soft skills: {distribution.get('soft', 0)}%")
            print(f"   - Strengths identified: {len(result['data'].get('strengths', []))}")
            print(f"   - Improvement areas: {len(result['data'].get('improvement_areas', []))}")
        else:
            print(f"❌ Skills analysis failed: {result.get('error')}")
        
    except Exception as e:
        print(f"❌ Skills analysis test failed: {str(e)}")
    
    # Test 5: Get recommendations
    print("\n💡 Test 5: Get recommendations")
    
    try:
        recommendations = await agent.get_recommendations(mock_user_profile.to_dict())
        print(f"✅ Recommendations generated: {len(recommendations)} items")
        
        for i, rec in enumerate(recommendations[:3]):  # Show first 3
            print(f"   {i+1}. {rec.get('title', 'No title')}")
        
    except Exception as e:
        print(f"❌ Recommendations test failed: {str(e)}")
    
    print("\n🎉 Skills Analysis Agent testing completed!")


if __name__ == "__main__":
    asyncio.run(test_skills_analysis_agent())