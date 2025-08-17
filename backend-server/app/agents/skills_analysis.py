"""
Skills Analysis Agent
Specialized AI agent for skills extraction, gap analysis, and learning recommendations
"""
import uuid
import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio

from app.agents.base import BaseAgent, AgentResponse
from app.models.user import UserProfile
from app.core.database import get_database
from app.integrations.watsonx import WatsonXClient
from app.integrations.langchain_utils import LangChainAgentManager

logger = logging.getLogger(__name__)


class SkillsAnalysisAgent(BaseAgent):
    """
    AI agent specialized in skills analysis, gap identification, and learning recommendations
    """
    
    def __init__(self, watsonx_client: WatsonXClient, langchain_manager: LangChainAgentManager = None):
        super().__init__(
            agent_id="skills_analysis_agent",
            watsonx_client=watsonx_client
        )
        self.watsonx_client = watsonx_client
        self.langchain_manager = langchain_manager
        
        # Predefined skill categories for better organization
        self.skill_categories = {
            "technical": ["programming", "software", "database", "cloud", "framework", "tool"],
            "soft": ["communication", "leadership", "teamwork", "problem-solving", "management"],
            "domain": ["finance", "healthcare", "marketing", "sales", "design", "analytics"],
            "certifications": ["certified", "certification", "license", "credential"]
        }
    
    async def process_request(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user request for skills analysis tasks
        """
        try:
            task_type = user_input.get("task_type", "analyze_skills")
            user_id = user_input.get("user_id")
            
            if not user_id:
                raise ValueError("user_id is required for skills analysis requests")
            
            result = await self.process_task(user_input)
            
            return AgentResponse(
                success=result.get("success", False),
                data=result.get("data"),
                error=result.get("error"),
                recommendations=result.get("recommendations", []),
                metadata=result.get("metadata", {})
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Error processing skills analysis request: {str(e)}")
            return AgentResponse(
                success=False,
                error=str(e)
            ).to_dict()
    
    async def get_recommendations(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate personalized skills development recommendations
        """
        try:
            user_id = user_profile.get("user_id") if isinstance(user_profile, dict) else user_profile.user_id
            
            task_data = {
                "task_type": "recommend_learning_paths",
                "user_id": user_id
            }
            
            result = await self.process_task(task_data)
            
            if result.get("success"):
                return result.get("recommendations", [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting skills recommendations: {str(e)}")
            return []
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process skills analysis tasks
        """
        try:
            task_type = task_data.get("task_type")
            user_id = task_data.get("user_id")
            
            if not user_id:
                raise ValueError("user_id is required for skills analysis tasks")
            
            # Create mock user profile for testing
            mock_user_profile = type('MockUserProfile', (), {
                'user_id': user_id,
                'skills': [],
                'certifications': [],
                'career_goals': {},
                'years_experience': 5,
                'industry': 'Technology',
                'updated_at': datetime.utcnow()
            })()
            
            # Mock database
            class MockDB:
                def add(self, obj): pass
                def commit(self): pass
            
            db = MockDB()
            
            if task_type == "extract_skills_from_resume":
                return await self._extract_skills_from_resume(mock_user_profile, task_data, db)
            elif task_type == "extract_skills_from_job":
                return await self._extract_skills_from_job(task_data, db)
            elif task_type == "analyze_skill_gaps":
                return await self._analyze_skill_gaps(mock_user_profile, task_data, db)
            elif task_type == "recommend_learning_paths":
                return await self._recommend_learning_paths(mock_user_profile, task_data, db)
            elif task_type == "analyze_skills":
                return await self._analyze_user_skills(mock_user_profile, task_data, db)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
        except Exception as e:
            logger.error(f"Error processing skills analysis task: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _extract_skills_from_resume(self, user_profile, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Extract skills from resume text using NLP
        """
        try:
            resume_text = task_data.get("resume_text", "")
            if not resume_text:
                raise ValueError("resume_text is required for skill extraction")
            
            # Use WatsonX.ai for skill extraction
            extraction_prompt = f"""
            Extract technical skills, soft skills, and certifications from the following resume text.
            Categorize them appropriately and include proficiency levels where mentioned.
            
            Resume Text:
            {resume_text}
            
            Return the results in JSON format:
            {{
                "technical_skills": [
                    {{"name": "Python", "category": "programming", "proficiency": "advanced", "years_experience": 5}},
                    {{"name": "AWS", "category": "cloud", "proficiency": "intermediate", "years_experience": 3}}
                ],
                "soft_skills": [
                    {{"name": "Leadership", "category": "management", "proficiency": "advanced"}},
                    {{"name": "Communication", "category": "interpersonal", "proficiency": "expert"}}
                ],
                "certifications": [
                    {{"name": "AWS Solutions Architect", "issuer": "Amazon", "year": 2023}},
                    {{"name": "PMP", "issuer": "PMI", "year": 2022}}
                ],
                "domain_expertise": [
                    {{"name": "Financial Services", "years_experience": 7}},
                    {{"name": "Data Analytics", "years_experience": 4}}
                ]
            }}
            """
            
            result = await self.watsonx_client.generate_text(extraction_prompt)
            
            if result["success"]:
                try:
                    extracted_data = json.loads(result["generated_text"])
                    
                    # Process and categorize skills
                    all_skills = []
                    
                    # Add technical skills
                    for skill in extracted_data.get("technical_skills", []):
                        all_skills.append({
                            "name": skill.get("name"),
                            "category": "technical",
                            "subcategory": skill.get("category", "general"),
                            "proficiency": skill.get("proficiency", "intermediate"),
                            "years_experience": skill.get("years_experience", 0),
                            "source": "resume",
                            "extracted_at": datetime.utcnow().isoformat()
                        })
                    
                    # Add soft skills
                    for skill in extracted_data.get("soft_skills", []):
                        all_skills.append({
                            "name": skill.get("name"),
                            "category": "soft",
                            "subcategory": skill.get("category", "general"),
                            "proficiency": skill.get("proficiency", "intermediate"),
                            "source": "resume",
                            "extracted_at": datetime.utcnow().isoformat()
                        })
                    
                    # Add certifications
                    certifications = []
                    for cert in extracted_data.get("certifications", []):
                        certifications.append({
                            "name": cert.get("name"),
                            "issuer": cert.get("issuer"),
                            "year": cert.get("year"),
                            "status": "active",
                            "extracted_at": datetime.utcnow().isoformat()
                        })
                    
                    # Add domain expertise
                    for domain in extracted_data.get("domain_expertise", []):
                        all_skills.append({
                            "name": domain.get("name"),
                            "category": "domain",
                            "subcategory": "expertise",
                            "years_experience": domain.get("years_experience", 0),
                            "source": "resume",
                            "extracted_at": datetime.utcnow().isoformat()
                        })
                    
                    return {
                        "success": True,
                        "data": {
                            "extracted_skills": all_skills,
                            "certifications": certifications,
                            "total_skills_extracted": len(all_skills)
                        },
                        "metadata": {
                            "extraction_method": "watsonx_nlp",
                            "resume_length": len(resume_text),
                            "processing_time": datetime.utcnow().isoformat()
                        }
                    }
                    
                except json.JSONDecodeError:
                    # Fallback to regex-based extraction
                    return await self._fallback_skill_extraction(resume_text, user_profile, db)
            else:
                # Fallback to regex-based extraction
                return await self._fallback_skill_extraction(resume_text, user_profile, db)
                
        except Exception as e:
            logger.error(f"Error extracting skills from resume: {str(e)}")
            raise
    
    async def _extract_skills_from_job(self, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Extract required skills from job description
        """
        try:
            job_description = task_data.get("job_description", "")
            job_title = task_data.get("job_title", "")
            
            if not job_description:
                raise ValueError("job_description is required for skill extraction")
            
            # Use WatsonX.ai for job skill extraction
            extraction_prompt = f"""
            Extract required skills, qualifications, and experience from this job posting.
            Focus on both technical requirements and soft skills mentioned.
            
            Job Title: {job_title}
            Job Description:
            {job_description}
            
            Return the results in JSON format:
            {{
                "required_skills": [
                    {{"name": "Python", "category": "technical", "importance": "high", "required_years": 3}},
                    {{"name": "Leadership", "category": "soft", "importance": "medium"}}
                ],
                "preferred_skills": [
                    {{"name": "Docker", "category": "technical", "importance": "low"}},
                    {{"name": "Agile", "category": "methodology", "importance": "medium"}}
                ],
                "required_experience": {{
                    "total_years": 5,
                    "specific_domains": ["web development", "API design"]
                }},
                "education_requirements": [
                    "Bachelor's degree in Computer Science",
                    "Master's degree preferred"
                ],
                "certifications": [
                    "AWS Certified Solutions Architect",
                    "Scrum Master Certification"
                ]
            }}
            """
            
            result = await self.watsonx_client.generate_text(extraction_prompt)
            
            if result["success"]:
                try:
                    extracted_data = json.loads(result["generated_text"])
                    
                    # Process extracted job requirements
                    job_skills = {
                        "required_skills": extracted_data.get("required_skills", []),
                        "preferred_skills": extracted_data.get("preferred_skills", []),
                        "required_experience": extracted_data.get("required_experience", {}),
                        "education_requirements": extracted_data.get("education_requirements", []),
                        "certifications": extracted_data.get("certifications", []),
                        "extraction_date": datetime.utcnow().isoformat()
                    }
                    
                    return {
                        "success": True,
                        "data": job_skills,
                        "metadata": {
                            "job_title": job_title,
                            "extraction_method": "watsonx_nlp",
                            "description_length": len(job_description)
                        }
                    }
                    
                except json.JSONDecodeError:
                    # Fallback to regex-based extraction
                    return await self._fallback_job_skill_extraction(job_description, job_title)
            else:
                # Fallback to regex-based extraction
                return await self._fallback_job_skill_extraction(job_description, job_title)
                
        except Exception as e:
            logger.error(f"Error extracting skills from job description: {str(e)}")
            raise
    
    async def _analyze_skill_gaps(self, user_profile, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Analyze skill gaps between user profile and target job/role
        """
        try:
            target_job_id = task_data.get("target_job_id")
            target_role = task_data.get("target_role")
            job_requirements = task_data.get("job_requirements", [])
            
            # Get user's current skills
            user_skills = user_profile.skills or []
            user_skill_names = [skill.get("name", "").lower() for skill in user_skills if isinstance(skill, dict)]
            
            # Get target requirements
            if target_job_id:
                # Extract skills from specific job
                job_extraction_result = await self._extract_skills_from_job({
                    "job_description": task_data.get("job_description", ""),
                    "job_title": task_data.get("job_title", "")
                }, db)
                
                if job_extraction_result["success"]:
                    job_data = job_extraction_result["data"]
                    required_skills = job_data.get("required_skills", [])
                    preferred_skills = job_data.get("preferred_skills", [])
                else:
                    required_skills = []
                    preferred_skills = []
            else:
                # Use provided requirements or analyze role
                required_skills = job_requirements
                preferred_skills = []
            
            # Perform gap analysis using WatsonX.ai
            gap_analysis_prompt = f"""
            Perform a comprehensive skill gap analysis between the user's current skills and target job requirements.
            
            User's Current Skills:
            {json.dumps(user_skills, indent=2)}
            
            Target Job Requirements:
            Required Skills: {json.dumps(required_skills, indent=2)}
            Preferred Skills: {json.dumps(preferred_skills, indent=2)}
            Target Role: {target_role}
            
            Analyze and provide:
            1. Skills the user already has that match requirements
            2. Critical skill gaps that must be addressed
            3. Nice-to-have skills that would strengthen the application
            4. Transferable skills that could be leveraged
            5. Priority order for skill development
            
            Return results in JSON format:
            {{
                "matching_skills": [
                    {{"name": "Python", "user_proficiency": "advanced", "required_level": "intermediate", "match_strength": "strong"}}
                ],
                "critical_gaps": [
                    {{"name": "Kubernetes", "required_level": "intermediate", "priority": "high", "estimated_learning_time": "3-6 months"}}
                ],
                "nice_to_have_gaps": [
                    {{"name": "GraphQL", "required_level": "basic", "priority": "low", "estimated_learning_time": "1-2 months"}}
                ],
                "transferable_skills": [
                    {{"user_skill": "Docker", "applicable_to": "Container Orchestration", "relevance": "high"}}
                ],
                "overall_readiness": {{
                    "percentage": 75,
                    "readiness_level": "good",
                    "key_strengths": ["Strong programming background", "Cloud experience"],
                    "main_concerns": ["Limited DevOps experience", "No Kubernetes knowledge"]
                }},
                "development_priority": [
                    {{"skill": "Kubernetes", "priority": 1, "reason": "Critical for role success"}},
                    {{"skill": "CI/CD", "priority": 2, "reason": "Important for workflow efficiency"}}
                ]
            }}
            """
            
            result = await self.watsonx_client.generate_text(gap_analysis_prompt)
            
            if result["success"]:
                try:
                    gap_analysis = json.loads(result["generated_text"])
                    
                    # Calculate additional metrics
                    total_required = len(required_skills) + len(preferred_skills)
                    matching_count = len(gap_analysis.get("matching_skills", []))
                    gap_count = len(gap_analysis.get("critical_gaps", []))
                    
                    gap_analysis["metrics"] = {
                        "total_requirements": total_required,
                        "skills_matched": matching_count,
                        "critical_gaps_count": gap_count,
                        "match_percentage": (matching_count / total_required * 100) if total_required > 0 else 0,
                        "analysis_date": datetime.utcnow().isoformat()
                    }
                    
                    return {
                        "success": True,
                        "data": gap_analysis,
                        "recommendations": self._generate_gap_recommendations(gap_analysis),
                        "metadata": {
                            "target_role": target_role,
                            "target_job_id": target_job_id,
                            "analysis_method": "watsonx_ai"
                        }
                    }
                    
                except json.JSONDecodeError:
                    # Fallback to basic gap analysis
                    return await self._basic_gap_analysis(user_skills, required_skills, preferred_skills)
            else:
                # Fallback to basic gap analysis
                return await self._basic_gap_analysis(user_skills, required_skills, preferred_skills)
                
        except Exception as e:
            logger.error(f"Error analyzing skill gaps: {str(e)}")
            raise
    
    async def _recommend_learning_paths(self, user_profile, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Generate personalized learning path recommendations
        """
        try:
            target_skills = task_data.get("target_skills", [])
            career_goals = user_profile.career_goals or {}
            current_skills = user_profile.skills or []
            
            # If no target skills provided, use career goals to determine them
            if not target_skills and career_goals:
                target_role = career_goals.get("target_role", "")
                if target_role:
                    # Generate target skills based on role
                    role_analysis_prompt = f"""
                    What are the key skills needed for a {target_role} role?
                    Provide a comprehensive list of technical and soft skills.
                    
                    Return as JSON array:
                    ["skill1", "skill2", "skill3"]
                    """
                    
                    result = await self.watsonx_client.generate_text(role_analysis_prompt)
                    if result["success"]:
                        try:
                            target_skills = json.loads(result["generated_text"])
                        except json.JSONDecodeError:
                            target_skills = []
            
            # Generate learning path recommendations
            learning_prompt = f"""
            Create personalized learning paths for skill development based on the user's profile and goals.
            
            User Profile:
            - Current Skills: {json.dumps(current_skills, indent=2)}
            - Years Experience: {user_profile.years_experience}
            - Industry: {user_profile.industry}
            - Career Goals: {json.dumps(career_goals, indent=2)}
            
            Target Skills to Develop: {target_skills}
            
            For each target skill, provide:
            1. Learning path with progressive steps
            2. Recommended courses and resources
            3. Estimated timeline
            4. Prerequisites and dependencies
            5. Practical projects to build experience
            
            Return in JSON format:
            {{
                "learning_paths": [
                    {{
                        "skill": "Machine Learning",
                        "current_level": "beginner",
                        "target_level": "intermediate",
                        "estimated_duration": "6-9 months",
                        "prerequisites": ["Python", "Statistics"],
                        "learning_steps": [
                            {{
                                "step": 1,
                                "title": "Foundation in Python for ML",
                                "duration": "4-6 weeks",
                                "resources": [
                                    {{"type": "course", "name": "Python for Data Science", "provider": "Coursera", "url": ""}},
                                    {{"type": "book", "name": "Python Machine Learning", "author": "Sebastian Raschka"}}
                                ]
                            }}
                        ],
                        "projects": [
                            {{"name": "Iris Classification", "difficulty": "beginner", "estimated_time": "1 week"}},
                            {{"name": "House Price Prediction", "difficulty": "intermediate", "estimated_time": "2-3 weeks"}}
                        ],
                        "certifications": [
                            {{"name": "Google ML Engineer", "provider": "Google Cloud", "difficulty": "intermediate"}}
                        ]
                    }}
                ],
                "overall_timeline": "12-18 months",
                "priority_order": ["Machine Learning", "Cloud Computing", "DevOps"],
                "budget_estimate": {{
                    "free_resources": 60,
                    "paid_courses": 500,
                    "certifications": 1200,
                    "total_estimated": 1700
                }}
            }}
            """
            
            result = await self.watsonx_client.generate_text(learning_prompt)
            
            if result["success"]:
                try:
                    learning_data = json.loads(result["generated_text"])
                    
                    # Enhance with additional recommendations
                    enhanced_paths = self._enhance_learning_paths(learning_data, user_profile)
                    
                    return {
                        "success": True,
                        "data": enhanced_paths,
                        "recommendations": self._generate_learning_recommendations(enhanced_paths),
                        "metadata": {
                            "user_experience_level": user_profile.years_experience,
                            "target_skills_count": len(target_skills),
                            "generation_date": datetime.utcnow().isoformat()
                        }
                    }
                    
                except json.JSONDecodeError:
                    # Fallback to basic learning recommendations
                    return await self._basic_learning_recommendations(target_skills, current_skills)
            else:
                # Fallback to basic learning recommendations
                return await self._basic_learning_recommendations(target_skills, current_skills)
                
        except Exception as e:
            logger.error(f"Error generating learning path recommendations: {str(e)}")
            raise
    
    async def _analyze_user_skills(self, user_profile, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Comprehensive analysis of user's current skills
        """
        try:
            current_skills = user_profile.skills or []
            
            # Analyze skills using WatsonX.ai
            analysis_prompt = f"""
            Analyze the user's skill profile and provide comprehensive insights.
            
            User Skills: {json.dumps(current_skills, indent=2)}
            Years Experience: {user_profile.years_experience}
            Industry: {user_profile.industry}
            
            Provide analysis on:
            1. Skill distribution across categories
            2. Strengths and areas for improvement
            3. Market demand for current skills
            4. Skill complementarity and synergies
            5. Career progression opportunities
            
            Return in JSON format:
            {{
                "skill_distribution": {{
                    "technical": 65,
                    "soft": 20,
                    "domain": 15
                }},
                "strengths": [
                    {{"category": "Programming", "skills": ["Python", "JavaScript"], "market_demand": "high"}},
                    {{"category": "Cloud", "skills": ["AWS", "Docker"], "market_demand": "very_high"}}
                ],
                "improvement_areas": [
                    {{"category": "Leadership", "current_level": "basic", "importance": "high", "reason": "Career advancement"}},
                    {{"category": "Data Science", "current_level": "none", "importance": "medium", "reason": "Industry trend"}}
                ],
                "market_analysis": {{
                    "high_demand_skills": ["Kubernetes", "Machine Learning", "React"],
                    "emerging_skills": ["AI/ML", "Blockchain", "Edge Computing"],
                    "declining_skills": ["jQuery", "Flash", "Legacy Systems"]
                }},
                "career_opportunities": [
                    {{"role": "Senior Developer", "match_percentage": 85, "missing_skills": ["Leadership"]}}
                ],
                "skill_synergies": [
                    {{"primary_skill": "Python", "complementary_skills": ["Data Science", "Machine Learning"], "benefit": "Full-stack data capabilities"}}
                ]
            }}
            """
            
            result = await self.watsonx_client.generate_text(analysis_prompt)
            
            if result["success"]:
                try:
                    analysis_data = json.loads(result["generated_text"])
                    
                    # Add calculated metrics
                    analysis_data["metrics"] = {
                        "total_skills": len(current_skills),
                        "skill_diversity_score": self._calculate_skill_diversity(current_skills),
                        "experience_alignment_score": self._calculate_experience_alignment(current_skills, user_profile.years_experience),
                        "analysis_date": datetime.utcnow().isoformat()
                    }
                    
                    return {
                        "success": True,
                        "data": analysis_data,
                        "recommendations": self._generate_skill_analysis_recommendations(analysis_data),
                        "metadata": {
                            "analysis_method": "watsonx_comprehensive",
                            "user_experience": user_profile.years_experience,
                            "industry": user_profile.industry
                        }
                    }
                    
                except json.JSONDecodeError:
                    # Fallback to basic analysis
                    return await self._basic_skill_analysis(current_skills, user_profile)
            else:
                # Fallback to basic analysis
                return await self._basic_skill_analysis(current_skills, user_profile)
                
        except Exception as e:
            logger.error(f"Error analyzing user skills: {str(e)}")
            raise
    
    # Helper methods
    
    async def _fallback_skill_extraction(self, text: str, user_profile, db) -> Dict[str, Any]:
        """Fallback skill extraction using regex patterns"""
        try:
            # Common skill patterns
            skill_patterns = {
                "programming": r'\b(python|java|javascript|c\+\+|c#|ruby|php|go|rust|swift|kotlin)\b',
                "web": r'\b(html|css|react|angular|vue|node\.js|express|django|flask)\b',
                "database": r'\b(sql|mysql|postgresql|mongodb|redis|elasticsearch)\b',
                "cloud": r'\b(aws|azure|gcp|docker|kubernetes|terraform)\b',
                "tools": r'\b(git|jenkins|jira|confluence|slack|figma)\b'
            }
            
            extracted_skills = []
            
            for category, pattern in skill_patterns.items():
                matches = re.findall(pattern, text.lower())
                for match in set(matches):  # Remove duplicates
                    extracted_skills.append({
                        "name": match.title(),
                        "category": "technical",
                        "subcategory": category,
                        "proficiency": "intermediate",
                        "source": "resume_regex",
                        "extracted_at": datetime.utcnow().isoformat()
                    })
            
            return {
                "success": True,
                "data": {
                    "extracted_skills": extracted_skills,
                    "total_skills_extracted": len(extracted_skills)
                },
                "metadata": {
                    "extraction_method": "regex_fallback",
                    "text_length": len(text)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in fallback skill extraction: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _fallback_job_skill_extraction(self, job_description: str, job_title: str) -> Dict[str, Any]:
        """Fallback job skill extraction using regex patterns"""
        try:
            # Extract skills using patterns
            required_skills = []
            preferred_skills = []
            
            # Basic extraction
            common_skills = ["python", "java", "javascript", "sql", "aws", "docker", "kubernetes", "react", "angular"]
            
            for skill in common_skills:
                if skill.lower() in job_description.lower():
                    required_skills.append({
                        "name": skill.title(),
                        "category": "technical",
                        "importance": "medium"
                    })
            
            return {
                "success": True,
                "data": {
                    "required_skills": required_skills,
                    "preferred_skills": preferred_skills,
                    "extraction_date": datetime.utcnow().isoformat()
                },
                "metadata": {
                    "extraction_method": "regex_fallback",
                    "job_title": job_title
                }
            }
            
        except Exception as e:
            logger.error(f"Error in fallback job skill extraction: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_gap_recommendations(self, gap_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on gap analysis"""
        recommendations = []
        
        critical_gaps = gap_analysis.get("critical_gaps", [])
        for gap in critical_gaps[:3]:  # Top 3 critical gaps
            recommendations.append({
                "type": "skill_development",
                "priority": "high",
                "title": f"Develop {gap.get('name')} skills",
                "description": f"Focus on learning {gap.get('name')} as it's critical for your target role",
                "estimated_time": gap.get("estimated_learning_time", "3-6 months"),
                "action_items": [
                    f"Find online courses for {gap.get('name')}",
                    f"Practice {gap.get('name')} through projects",
                    f"Consider certification in {gap.get('name')}"
                ]
            })
        
        return recommendations
    
    def _enhance_learning_paths(self, learning_data: Dict[str, Any], user_profile) -> Dict[str, Any]:
        """Enhance learning paths with user-specific information"""
        # Add user context to learning paths
        enhanced_data = learning_data.copy()
        
        # Adjust timelines based on user experience
        experience_multiplier = 1.0
        if user_profile.years_experience > 5:
            experience_multiplier = 0.8  # Experienced users learn faster
        elif user_profile.years_experience < 2:
            experience_multiplier = 1.3  # Beginners need more time
        
        for path in enhanced_data.get("learning_paths", []):
            # Adjust duration
            if "estimated_duration" in path:
                # This is a simplified adjustment - in practice, you'd parse and recalculate
                path["adjusted_for_experience"] = True
                path["experience_level"] = user_profile.years_experience
        
        return enhanced_data
    
    def _generate_learning_recommendations(self, learning_paths: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable learning recommendations"""
        recommendations = []
        
        for path in learning_paths.get("learning_paths", [])[:3]:  # Top 3 paths
            recommendations.append({
                "type": "learning_path",
                "priority": "medium",
                "title": f"Start learning {path.get('skill')}",
                "description": f"Begin your {path.get('skill')} learning journey",
                "estimated_time": path.get("estimated_duration"),
                "action_items": [
                    "Review prerequisites",
                    "Enroll in recommended courses",
                    "Set up practice environment",
                    "Plan first project"
                ]
            })
        
        return recommendations
    
    def _calculate_skill_diversity(self, skills: List[Dict]) -> float:
        """Calculate skill diversity score"""
        if not skills:
            return 0.0
        
        categories = set()
        for skill in skills:
            if isinstance(skill, dict):
                categories.add(skill.get("category", "unknown"))
        
        # Diversity score based on category spread
        return min(len(categories) / 5.0, 1.0)  # Normalize to 0-1
    
    def _calculate_experience_alignment(self, skills: List[Dict], years_experience: int) -> float:
        """Calculate how well skills align with experience level"""
        if not skills or not years_experience:
            return 0.5
        
        advanced_skills = sum(1 for skill in skills 
                            if isinstance(skill, dict) and 
                            skill.get("proficiency") in ["advanced", "expert"])
        
        expected_advanced = max(1, years_experience // 2)  # Expect 1 advanced skill per 2 years
        
        return min(advanced_skills / expected_advanced, 1.0)
    
    async def _basic_gap_analysis(self, user_skills: List[Dict], required_skills: List[Dict], preferred_skills: List[Dict]) -> Dict[str, Any]:
        """Basic gap analysis fallback"""
        user_skill_names = {skill.get("name", "").lower() for skill in user_skills if isinstance(skill, dict)}
        
        matching_skills = []
        critical_gaps = []
        
        for req_skill in required_skills:
            skill_name = req_skill.get("name", "").lower()
            if skill_name in user_skill_names:
                matching_skills.append(req_skill)
            else:
                critical_gaps.append(req_skill)
        
        return {
            "success": True,
            "data": {
                "matching_skills": matching_skills,
                "critical_gaps": critical_gaps,
                "overall_readiness": {
                    "percentage": len(matching_skills) / max(len(required_skills), 1) * 100,
                    "readiness_level": "basic_analysis"
                }
            },
            "metadata": {
                "analysis_method": "basic_fallback"
            }
        }
    
    async def _basic_learning_recommendations(self, target_skills: List[str], current_skills: List[Dict]) -> Dict[str, Any]:
        """Basic learning recommendations fallback"""
        current_skill_names = {skill.get("name", "").lower() for skill in current_skills if isinstance(skill, dict)}
        
        learning_paths = []
        for skill in target_skills:
            if skill.lower() not in current_skill_names:
                learning_paths.append({
                    "skill": skill,
                    "current_level": "beginner",
                    "target_level": "intermediate",
                    "estimated_duration": "3-6 months",
                    "learning_steps": [
                        {
                            "step": 1,
                            "title": f"Learn {skill} basics",
                            "duration": "4-6 weeks"
                        }
                    ]
                })
        
        return {
            "success": True,
            "data": {
                "learning_paths": learning_paths,
                "overall_timeline": "6-12 months"
            },
            "metadata": {
                "generation_method": "basic_fallback"
            }
        }
    
    async def _basic_skill_analysis(self, current_skills: List[Dict], user_profile) -> Dict[str, Any]:
        """Basic skill analysis fallback"""
        technical_count = sum(1 for skill in current_skills 
                            if isinstance(skill, dict) and skill.get("category") == "technical")
        soft_count = sum(1 for skill in current_skills 
                       if isinstance(skill, dict) and skill.get("category") == "soft")
        
        return {
            "success": True,
            "data": {
                "skill_distribution": {
                    "technical": technical_count,
                    "soft": soft_count,
                    "total": len(current_skills)
                },
                "strengths": ["Technical skills"] if technical_count > 5 else [],
                "improvement_areas": ["Soft skills"] if soft_count < 3 else []
            },
            "metadata": {
                "analysis_method": "basic_fallback"
            }
        }
    
    def _generate_skill_analysis_recommendations(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations from skill analysis"""
        recommendations = []
        
        improvement_areas = analysis_data.get("improvement_areas", [])
        for area in improvement_areas[:2]:  # Top 2 improvement areas
            recommendations.append({
                "type": "skill_improvement",
                "priority": "medium",
                "title": f"Improve {area.get('category')} skills",
                "description": f"Focus on developing {area.get('category')} skills for career advancement",
                "reason": area.get("reason", "Career development"),
                "action_items": [
                    f"Identify specific {area.get('category')} skills to develop",
                    f"Find learning resources for {area.get('category')}",
                    f"Practice {area.get('category')} skills in current role"
                ]
            })
        
        return recommendations   
 
    # Abstract method implementations required by BaseAgent
    
    async def _process_request_impl(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementation of request processing for skills analysis
        """
        try:
            task_type = user_input.get("task_type", "analyze_skills")
            user_id = user_input.get("user_id") or context.get("user_id")
            
            if not user_id:
                raise ValueError("user_id is required for skills analysis requests")
            
            # Process the request using existing process_task method
            result = await self.process_task(user_input)
            
            return {
                "success": result.get("success", False),
                "data": result.get("data"),
                "error": result.get("error"),
                "recommendations": result.get("recommendations", []),
                "metadata": result.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Error in _process_request_impl: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "recommendations": [],
                "metadata": {"error_timestamp": datetime.utcnow().isoformat()}
            }
    
    async def _get_recommendations_impl(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Implementation of recommendations generation for skills analysis
        """
        try:
            user_id = user_profile.get("user_id") if isinstance(user_profile, dict) else getattr(user_profile, 'user_id', None)
            
            if not user_id:
                return []
            
            # Generate learning path recommendations
            task_data = {
                "task_type": "recommend_learning_paths",
                "user_id": user_id,
                "target_skills": user_profile.get("target_skills", []),
                "career_goals": user_profile.get("career_goals", {})
            }
            
            result = await self.process_task(task_data)
            
            if result.get("success"):
                recommendations = result.get("recommendations", [])
                if not recommendations:
                    # Extract recommendations from data if not in recommendations field
                    data = result.get("data", {})
                    learning_paths = data.get("learning_paths", [])
                    recommendations = []
                    
                    for path in learning_paths:
                        recommendations.append({
                            "type": "learning_path",
                            "skill": path.get("skill"),
                            "priority": "high" if path.get("skill") in ["Python", "Machine Learning", "Cloud Computing"] else "medium",
                            "description": f"Learn {path.get('skill')} - estimated duration: {path.get('estimated_duration', 'N/A')}",
                            "action": "start_learning",
                            "metadata": {
                                "duration": path.get("estimated_duration"),
                                "difficulty": path.get("target_level", "intermediate"),
                                "prerequisites": path.get("prerequisites", [])
                            }
                        })
                
                return recommendations
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error in _get_recommendations_impl: {str(e)}")
            return []