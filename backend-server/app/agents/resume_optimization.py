"""
Resume Optimization Agent
Specialized AI agent for resume parsing, optimization, and ATS compatibility
"""
import uuid
import logging
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from app.agents.base import BaseAgent, AgentResponse
from app.models.resume import Resume, ResumeAnalysis, ResumeOptimization, ResumeTemplate
from app.models.job import Job
from app.models.user import UserProfile
from app.core.database import get_database
from app.integrations.watsonx import WatsonXClient

logger = logging.getLogger(__name__)


class ResumeOptimizationAgent(BaseAgent):
    """
    AI agent specialized in resume optimization and ATS compatibility
    """
    
    def __init__(self, watsonx_client: WatsonXClient):
        super().__init__(
            agent_id="resume_optimization_agent",
            watsonx_client=watsonx_client
        )
        self.watsonx_client = watsonx_client
        
        # ATS keywords and patterns
        self.ats_keywords = {
            'action_verbs': [
                'achieved', 'managed', 'led', 'developed', 'implemented', 'created',
                'improved', 'increased', 'reduced', 'optimized', 'designed', 'built',
                'delivered', 'executed', 'coordinated', 'collaborated', 'analyzed'
            ],
            'technical_skills': [
                'python', 'javascript', 'react', 'node.js', 'sql', 'aws', 'docker',
                'kubernetes', 'git', 'agile', 'scrum', 'machine learning', 'ai'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem-solving',
                'analytical', 'creative', 'adaptable', 'detail-oriented'
            ]
        }
    
    async def process_request(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user request for resume optimization tasks
        
        Args:
            user_input: User request data
            context: Current conversation/session context
            
        Returns:
            Structured response with optimization results
        """
        try:
            task_type = user_input.get("task_type", "optimize_resume")
            user_id = user_input.get("user_id")
            
            if not user_id:
                raise ValueError("user_id is required for resume optimization requests")
            
            return await self.process_task(user_input)
            
        except Exception as e:
            logger.error(f"Error processing resume optimization request: {str(e)}")
            return AgentResponse(
                success=False,
                error=str(e)
            ).to_dict()
    
    async def get_recommendations(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate personalized resume recommendations based on user profile
        
        Args:
            user_profile: User profile data
            
        Returns:
            List of resume optimization recommendations
        """
        try:
            user_id = user_profile.get("user_id") if isinstance(user_profile, dict) else user_profile.user_id
            
            task_data = {
                "task_type": "get_resume_recommendations",
                "user_id": user_id
            }
            
            result = await self.process_task(task_data)
            
            if result.get("success"):
                return result.get("recommendations", [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting resume recommendations: {str(e)}")
            return []
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process resume optimization tasks
        
        Args:
            task_data: Task information including user_id and task type
            
        Returns:
            Task processing results
        """
        try:
            task_type = task_data.get("task_type")
            user_id = task_data.get("user_id")
            
            if not user_id:
                raise ValueError("user_id is required for resume optimization tasks")
            
            # Get database session
            db = next(get_database())
            
            if task_type == "parse_resume":
                return await self._parse_resume(task_data, db)
            elif task_type == "optimize_resume":
                return await self._optimize_resume(task_data, db)
            elif task_type == "analyze_ats_compatibility":
                return await self._analyze_ats_compatibility(task_data, db)
            elif task_type == "generate_resume":
                return await self._generate_resume(task_data, db)
            elif task_type == "get_resume_recommendations":
                return await self._get_resume_recommendations(task_data, db)
            elif task_type == "score_resume":
                return await self._score_resume(task_data, db)
            elif task_type == "compare_resumes":
                return await self._compare_resumes(task_data, db)
            elif task_type == "calculate_acceptance_probability":
                return await self._calculate_acceptance_probability(task_data, db)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
        except Exception as e:
            logger.error(f"Error processing resume optimization task: {str(e)}")
            return AgentResponse(
                success=False,
                error=str(e)
            ).to_dict()
    
    async def _parse_resume(self, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Parse resume content and extract structured information
        
        Args:
            task_data: Task parameters including resume content
            db: Database session
            
        Returns:
            Parsed resume data
        """
        try:
            resume_content = task_data.get("resume_content")
            resume_file = task_data.get("resume_file")
            user_id = task_data.get("user_id")
            
            if not resume_content and not resume_file:
                raise ValueError("Either resume_content or resume_file is required")
            
            # If file provided, extract text content (simplified for now)
            if resume_file and not resume_content:
                resume_content = resume_file.get("content", "")
            
            # Use WatsonX.ai to parse resume content
            parsing_prompt = f"""
            Parse the following resume content and extract structured information:
            
            RESUME CONTENT:
            {resume_content}
            
            Extract and format as JSON:
            {{
                "personal_info": {{
                    "name": "Full Name",
                    "email": "email@example.com",
                    "phone": "phone number",
                    "location": "city, state",
                    "linkedin": "linkedin profile",
                    "website": "personal website"
                }},
                "professional_summary": "Professional summary text",
                "experience": [
                    {{
                        "title": "Job Title",
                        "company": "Company Name",
                        "location": "Location",
                        "start_date": "MM/YYYY",
                        "end_date": "MM/YYYY or Present",
                        "description": "Job description and achievements",
                        "achievements": ["Achievement 1", "Achievement 2"]
                    }}
                ],
                "education": [
                    {{
                        "degree": "Degree Type",
                        "field": "Field of Study",
                        "institution": "Institution Name",
                        "graduation_date": "MM/YYYY",
                        "gpa": "GPA if mentioned"
                    }}
                ],
                "skills": [
                    {{
                        "category": "Technical Skills",
                        "skills": ["Skill 1", "Skill 2", "Skill 3"]
                    }}
                ],
                "certifications": [
                    {{
                        "name": "Certification Name",
                        "issuer": "Issuing Organization",
                        "date": "MM/YYYY",
                        "expiry": "MM/YYYY or null"
                    }}
                ],
                "projects": [
                    {{
                        "name": "Project Name",
                        "description": "Project description",
                        "technologies": ["Tech 1", "Tech 2"],
                        "url": "project url if available"
                    }}
                ]
            }}
            
            Ensure all dates are in MM/YYYY format and extract as much relevant information as possible.
            """
            
            result = await self.watsonx_client.generate_text(parsing_prompt)
            
            if result["success"]:
                try:
                    parsed_data = json.loads(result["generated_text"])
                    
                    # Create resume record
                    resume_id = str(uuid.uuid4())
                    resume = Resume(
                        resume_id=resume_id,
                        user_id=user_id,
                        version=1,
                        title=f"Resume - {datetime.now().strftime('%Y-%m-%d')}",
                        content=parsed_data,
                        raw_text=resume_content
                    )
                    
                    db.add(resume)
                    db.commit()
                    
                    return AgentResponse(
                        success=True,
                        data={
                            "resume_id": resume_id,
                            "parsed_content": parsed_data
                        },
                        metadata={"parsing_method": "watsonx_ai"}
                    ).to_dict()
                    
                except json.JSONDecodeError:
                    # Fallback to basic parsing
                    basic_parsed = await self._basic_resume_parsing(resume_content)
                    
                    resume_id = str(uuid.uuid4())
                    resume = Resume(
                        resume_id=resume_id,
                        user_id=user_id,
                        version=1,
                        title=f"Resume - {datetime.now().strftime('%Y-%m-%d')}",
                        content=basic_parsed,
                        raw_text=resume_content
                    )
                    
                    db.add(resume)
                    db.commit()
                    
                    return AgentResponse(
                        success=True,
                        data={
                            "resume_id": resume_id,
                            "parsed_content": basic_parsed
                        },
                        metadata={"parsing_method": "basic_fallback"}
                    ).to_dict()
            else:
                raise Exception("Failed to parse resume with AI")
                
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            raise
    
    async def _optimize_resume(self, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Optimize resume for specific job or general ATS compatibility
        
        Args:
            task_data: Task parameters including resume_id and job_id
            db: Database session
            
        Returns:
            Optimized resume data
        """
        try:
            resume_id = task_data.get("resume_id")
            job_id = task_data.get("job_id")
            optimization_type = task_data.get("optimization_type", "ats")
            
            if not resume_id:
                raise ValueError("resume_id is required for optimization")
            
            # Get resume
            resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
            if not resume:
                raise ValueError(f"Resume not found: {resume_id}")
            
            # Get job if specified
            job = None
            if job_id:
                job = db.query(Job).filter(Job.job_id == job_id).first()
                if not job:
                    raise ValueError(f"Job not found: {job_id}")
            
            # Generate optimization recommendations
            optimization_prompt = self._build_optimization_prompt(resume, job, optimization_type)
            result = await self.watsonx_client.generate_text(optimization_prompt)
            
            if result["success"]:
                try:
                    optimization_data = json.loads(result["generated_text"])
                    
                    # Create optimized resume version
                    optimized_resume_id = str(uuid.uuid4())
                    optimized_content = self._apply_optimizations(
                        resume.content, 
                        optimization_data.get("optimizations", [])
                    )
                    
                    optimized_resume = Resume(
                        resume_id=optimized_resume_id,
                        user_id=resume.user_id,
                        version=resume.version + 1,
                        title=f"{resume.title} - Optimized",
                        content=optimized_content,
                        target_job_id=job_id,
                        ats_score=optimization_data.get("estimated_ats_score", 0.8),
                        optimization_suggestions=optimization_data.get("suggestions", [])
                    )
                    
                    db.add(optimized_resume)
                    
                    # Create optimization record
                    optimization_record = ResumeOptimization(
                        optimization_id=str(uuid.uuid4()),
                        original_resume_id=resume_id,
                        optimized_resume_id=optimized_resume_id,
                        job_id=job_id,
                        optimization_type=optimization_type,
                        changes_made=optimization_data.get("changes", []),
                        score_improvement=optimization_data.get("score_improvement", 0.0)
                    )
                    
                    db.add(optimization_record)
                    db.commit()
                    
                    return AgentResponse(
                        success=True,
                        data={
                            "original_resume_id": resume_id,
                            "optimized_resume_id": optimized_resume_id,
                            "optimizations": optimization_data.get("optimizations", []),
                            "ats_score": optimization_data.get("estimated_ats_score", 0.8),
                            "improvements": optimization_data.get("improvements", [])
                        },
                        recommendations=optimization_data.get("suggestions", [])
                    ).to_dict()
                    
                except json.JSONDecodeError:
                    # Fallback optimization
                    basic_optimizations = await self._basic_optimization(resume, job)
                    
                    return AgentResponse(
                        success=True,
                        data=basic_optimizations,
                        metadata={"optimization_method": "basic_fallback"}
                    ).to_dict()
            else:
                raise Exception("Failed to generate optimizations")
                
        except Exception as e:
            logger.error(f"Error optimizing resume: {str(e)}")
            raise
    
    async def _analyze_ats_compatibility(self, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Analyze resume for ATS compatibility and scoring
        
        Args:
            task_data: Task parameters including resume_id
            db: Database session
            
        Returns:
            ATS compatibility analysis
        """
        try:
            resume_id = task_data.get("resume_id")
            job_id = task_data.get("job_id")
            
            if not resume_id:
                raise ValueError("resume_id is required for ATS analysis")
            
            # Get resume
            resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
            if not resume:
                raise ValueError(f"Resume not found: {resume_id}")
            
            # Get job if specified
            job = None
            if job_id:
                job = db.query(Job).filter(Job.job_id == job_id).first()
            
            # Perform ATS analysis
            ats_analysis = await self._perform_ats_analysis(resume, job)
            
            # Create analysis record
            analysis_id = str(uuid.uuid4())
            analysis = ResumeAnalysis(
                analysis_id=analysis_id,
                resume_id=resume_id,
                job_id=job_id,
                ats_score=ats_analysis["ats_score"],
                keyword_analysis=ats_analysis["keyword_analysis"],
                section_analysis=ats_analysis["section_analysis"],
                formatting_analysis=ats_analysis["formatting_analysis"],
                improvement_suggestions=ats_analysis["suggestions"],
                content_score=ats_analysis.get("content_score", 0.7),
                format_score=ats_analysis.get("format_score", 0.8),
                keyword_score=ats_analysis.get("keyword_score", 0.6),
                readability_score=ats_analysis.get("readability_score", 0.7),
                analysis_type="ats_compatibility"
            )
            
            db.add(analysis)
            db.commit()
            
            return AgentResponse(
                success=True,
                data={
                    "analysis_id": analysis_id,
                    "ats_score": ats_analysis["ats_score"],
                    "detailed_analysis": ats_analysis
                },
                recommendations=ats_analysis["suggestions"]
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Error analyzing ATS compatibility: {str(e)}")
            raise
    
    async def _generate_resume(self, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Generate new resume from user profile and job requirements
        
        Args:
            task_data: Task parameters including user_id and job_id
            db: Database session
            
        Returns:
            Generated resume data
        """
        try:
            user_id = task_data.get("user_id")
            job_id = task_data.get("job_id")
            template_id = task_data.get("template_id")
            
            # Get user profile
            user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not user_profile:
                raise ValueError(f"User profile not found: {user_id}")
            
            # Get job if specified
            job = None
            if job_id:
                job = db.query(Job).filter(Job.job_id == job_id).first()
            
            # Get template if specified
            template = None
            if template_id:
                template = db.query(ResumeTemplate).filter(ResumeTemplate.template_id == template_id).first()
            
            # Generate resume content
            generation_prompt = self._build_generation_prompt(user_profile, job, template)
            result = await self.watsonx_client.generate_text(generation_prompt)
            
            if result["success"]:
                try:
                    generated_content = json.loads(result["generated_text"])
                    
                    # Create resume record
                    resume_id = str(uuid.uuid4())
                    resume = Resume(
                        resume_id=resume_id,
                        user_id=user_id,
                        version=1,
                        title=f"Generated Resume - {job.title if job else 'General'}",
                        content=generated_content,
                        target_job_id=job_id,
                        template_id=template_id
                    )
                    
                    db.add(resume)
                    db.commit()
                    
                    return AgentResponse(
                        success=True,
                        data={
                            "resume_id": resume_id,
                            "content": generated_content
                        },
                        metadata={"generation_method": "watsonx_ai"}
                    ).to_dict()
                    
                except json.JSONDecodeError:
                    # Fallback generation
                    basic_content = await self._basic_resume_generation(user_profile, job)
                    
                    resume_id = str(uuid.uuid4())
                    resume = Resume(
                        resume_id=resume_id,
                        user_id=user_id,
                        version=1,
                        title=f"Generated Resume - {job.title if job else 'General'}",
                        content=basic_content,
                        target_job_id=job_id
                    )
                    
                    db.add(resume)
                    db.commit()
                    
                    return AgentResponse(
                        success=True,
                        data={
                            "resume_id": resume_id,
                            "content": basic_content
                        },
                        metadata={"generation_method": "basic_fallback"}
                    ).to_dict()
            else:
                raise Exception("Failed to generate resume content")
                
        except Exception as e:
            logger.error(f"Error generating resume: {str(e)}")
            raise
    
    async def _get_resume_recommendations(self, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Get resume optimization recommendations for user
        
        Args:
            task_data: Task parameters including user_id
            db: Database session
            
        Returns:
            Resume recommendations
        """
        try:
            user_id = task_data.get("user_id")
            
            # Get user's resumes
            resumes = db.query(Resume).filter(
                Resume.user_id == user_id,
                Resume.is_active == True
            ).all()
            
            recommendations = []
            
            for resume in resumes:
                # Analyze each resume
                analysis = await self._perform_ats_analysis(resume, None)
                
                recommendations.append({
                    "resume_id": resume.resume_id,
                    "title": resume.title,
                    "ats_score": analysis["ats_score"],
                    "priority_improvements": analysis["suggestions"][:3],
                    "last_updated": resume.updated_at.isoformat()
                })
            
            # Sort by ATS score (lowest first - needs most improvement)
            recommendations.sort(key=lambda x: x["ats_score"])
            
            return AgentResponse(
                success=True,
                recommendations=recommendations,
                data={"total_resumes": len(resumes)}
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Error getting resume recommendations: {str(e)}")
            raise
    
    async def _score_resume(self, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Score resume against job requirements
        
        Args:
            task_data: Task parameters including resume_id and job_id
            db: Database session
            
        Returns:
            Resume scoring results
        """
        try:
            resume_id = task_data.get("resume_id")
            job_id = task_data.get("job_id")
            
            if not resume_id:
                raise ValueError("resume_id is required for scoring")
            
            # Get resume
            resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
            if not resume:
                raise ValueError(f"Resume not found: {resume_id}")
            
            # Get job if specified
            job = None
            if job_id:
                job = db.query(Job).filter(Job.job_id == job_id).first()
            
            # Calculate scores
            scoring_result = await self._calculate_resume_scores(resume, job)
            
            return AgentResponse(
                success=True,
                data=scoring_result
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Error scoring resume: {str(e)}")
            raise
    
    # Helper methods
    
    async def _basic_resume_parsing(self, resume_content: str) -> Dict[str, Any]:
        """Basic fallback resume parsing using regex patterns"""
        parsed = {
            "personal_info": {},
            "professional_summary": "",
            "experience": [],
            "education": [],
            "skills": [],
            "certifications": [],
            "projects": []
        }
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, resume_content)
        if emails:
            parsed["personal_info"]["email"] = emails[0]
        
        # Extract phone
        phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phones = re.findall(phone_pattern, resume_content)
        if phones:
            parsed["personal_info"]["phone"] = ''.join(phones[0])
        
        return parsed
    
    def _build_optimization_prompt(self, resume: Resume, job: Job, optimization_type: str) -> str:
        """Build prompt for resume optimization"""
        job_context = ""
        if job:
            job_context = f"""
            TARGET JOB:
            - Title: {job.title}
            - Company: {job.company}
            - Requirements: {job.requirements}
            - Qualifications: {job.qualifications}
            - Description: {job.description[:500] if job.description else 'N/A'}
            """
        
        return f"""
        Optimize the following resume for {optimization_type} compatibility:
        
        CURRENT RESUME:
        {json.dumps(resume.content, indent=2)}
        
        {job_context}
        
        Provide optimization recommendations in JSON format:
        {{
            "estimated_ats_score": 0.85,
            "optimizations": [
                {{
                    "section": "experience",
                    "change": "Add quantified achievements",
                    "before": "Managed team",
                    "after": "Managed team of 8 developers, increasing productivity by 25%"
                }}
            ],
            "suggestions": [
                "Add more action verbs",
                "Include relevant keywords",
                "Quantify achievements"
            ],
            "improvements": [
                "Better keyword density",
                "Improved ATS readability"
            ],
            "score_improvement": 0.15
        }}
        """
    
    def _build_generation_prompt(self, user_profile: UserProfile, job: Job, template: ResumeTemplate) -> str:
        """Build prompt for resume generation"""
        job_context = ""
        if job:
            job_context = f"""
            TARGET JOB:
            - Title: {job.title}
            - Company: {job.company}
            - Requirements: {job.requirements}
            - Qualifications: {job.qualifications}
            """
        
        template_context = ""
        if template:
            template_context = f"""
            TEMPLATE STRUCTURE:
            {json.dumps(template.sections, indent=2)}
            """
        
        return f"""
        Generate a professional resume based on the following user profile:
        
        USER PROFILE:
        - Name: {user_profile.first_name} {user_profile.last_name}
        - Current Title: {user_profile.current_title}
        - Experience: {user_profile.years_experience} years
        - Skills: {user_profile.skills}
        - Experience: {user_profile.experience}
        - Education: {user_profile.education}
        
        {job_context}
        {template_context}
        
        Generate resume content in JSON format with sections:
        personal_info, professional_summary, experience, education, skills, certifications, projects
        """
    
    def _apply_optimizations(self, content: Dict[str, Any], optimizations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply optimization changes to resume content"""
        optimized_content = content.copy()
        
        for optimization in optimizations:
            section = optimization.get("section")
            if section in optimized_content:
                # Apply the optimization (simplified implementation)
                pass
        
        return optimized_content
    
    async def _perform_ats_analysis(self, resume: Resume, job: Job) -> Dict[str, Any]:
        """Perform comprehensive ATS analysis"""
        content = resume.content
        
        # Keyword analysis
        keyword_analysis = self._analyze_keywords(content, job)
        
        # Section analysis
        section_analysis = self._analyze_sections(content)
        
        # Formatting analysis
        formatting_analysis = self._analyze_formatting(content)
        
        # Calculate overall ATS score
        ats_score = (
            keyword_analysis["score"] * 0.4 +
            section_analysis["score"] * 0.3 +
            formatting_analysis["score"] * 0.3
        )
        
        return {
            "ats_score": ats_score,
            "keyword_analysis": keyword_analysis,
            "section_analysis": section_analysis,
            "formatting_analysis": formatting_analysis,
            "suggestions": self._generate_suggestions(keyword_analysis, section_analysis, formatting_analysis)
        }
    
    def _analyze_keywords(self, content: Dict[str, Any], job: Job) -> Dict[str, Any]:
        """Analyze keyword density and relevance"""
        # Extract text from resume content
        resume_text = json.dumps(content).lower()
        
        # Count action verbs
        action_verb_count = sum(1 for verb in self.ats_keywords['action_verbs'] if verb in resume_text)
        
        # Count technical skills
        tech_skill_count = sum(1 for skill in self.ats_keywords['technical_skills'] if skill in resume_text)
        
        # Job-specific keywords if job provided
        job_keyword_count = 0
        if job and job.requirements:
            job_keywords = [req.lower() for req in job.requirements if isinstance(req, str)]
            job_keyword_count = sum(1 for keyword in job_keywords if keyword in resume_text)
        
        # Calculate keyword score
        total_keywords = len(self.ats_keywords['action_verbs']) + len(self.ats_keywords['technical_skills'])
        if job and job.requirements:
            total_keywords += len([req for req in job.requirements if isinstance(req, str)])
        
        keyword_score = min((action_verb_count + tech_skill_count + job_keyword_count) / max(total_keywords, 1), 1.0)
        
        return {
            "score": keyword_score,
            "action_verbs": action_verb_count,
            "technical_skills": tech_skill_count,
            "job_keywords": job_keyword_count,
            "density": keyword_score
        }
    
    def _analyze_sections(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resume sections completeness"""
        required_sections = ["personal_info", "experience", "education", "skills"]
        optional_sections = ["professional_summary", "certifications", "projects"]
        
        present_required = sum(1 for section in required_sections if section in content and content[section])
        present_optional = sum(1 for section in optional_sections if section in content and content[section])
        
        section_score = (present_required / len(required_sections)) * 0.8 + (present_optional / len(optional_sections)) * 0.2
        
        return {
            "score": section_score,
            "required_sections": present_required,
            "optional_sections": present_optional,
            "missing_sections": [section for section in required_sections if section not in content or not content[section]]
        }
    
    def _analyze_formatting(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resume formatting and structure"""
        # Check for consistent formatting (simplified)
        formatting_score = 0.8  # Default good formatting score
        
        # Check if experience has proper structure
        if "experience" in content and isinstance(content["experience"], list):
            for exp in content["experience"]:
                if isinstance(exp, dict) and all(key in exp for key in ["title", "company"]):
                    formatting_score += 0.05
        
        formatting_score = min(formatting_score, 1.0)
        
        return {
            "score": formatting_score,
            "structure_quality": "good",
            "consistency": "high"
        }
    
    def _generate_suggestions(self, keyword_analysis: Dict, section_analysis: Dict, formatting_analysis: Dict) -> List[str]:
        """Generate improvement suggestions based on analysis"""
        suggestions = []
        
        if keyword_analysis["score"] < 0.6:
            suggestions.append("Add more relevant keywords and action verbs")
        
        if section_analysis["score"] < 0.8:
            suggestions.extend([f"Add missing section: {section}" for section in section_analysis["missing_sections"]])
        
        if formatting_analysis["score"] < 0.7:
            suggestions.append("Improve resume formatting and structure")
        
        return suggestions
    
    async def _basic_optimization(self, resume: Resume, job: Job) -> Dict[str, Any]:
        """Basic fallback optimization"""
        return {
            "optimizations": ["Add more action verbs", "Include relevant keywords"],
            "ats_score": 0.75,
            "improvements": ["Better keyword density"]
        }
    
    async def _basic_resume_generation(self, user_profile: UserProfile, job: Job) -> Dict[str, Any]:
        """Basic fallback resume generation"""
        return {
            "personal_info": {
                "name": f"{user_profile.first_name} {user_profile.last_name}",
                "email": user_profile.email
            },
            "professional_summary": f"Experienced {user_profile.current_title} with {user_profile.years_experience} years of experience",
            "experience": user_profile.experience or [],
            "education": user_profile.education or [],
            "skills": user_profile.skills or []
        }
    
    async def _calculate_resume_scores(self, resume: Resume, job: Job) -> Dict[str, Any]:
        """Calculate detailed resume scores"""
        analysis = await self._perform_ats_analysis(resume, job)
        
        return {
            "overall_score": analysis["ats_score"],
            "keyword_score": analysis["keyword_analysis"]["score"],
            "section_score": analysis["section_analysis"]["score"],
            "formatting_score": analysis["formatting_analysis"]["score"],
            "detailed_analysis": analysis
        }  
  
    async def _compare_resumes(self, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Compare two resume versions and show differences
        
        Args:
            task_data: Task parameters including resume IDs
            db: Database session
            
        Returns:
            Resume comparison results
        """
        try:
            resume_id_1 = task_data.get("resume_id_1")
            resume_id_2 = task_data.get("resume_id_2")
            
            if not resume_id_1 or not resume_id_2:
                raise ValueError("Both resume_id_1 and resume_id_2 are required")
            
            # Get both resumes
            resume1 = db.query(Resume).filter(Resume.resume_id == resume_id_1).first()
            resume2 = db.query(Resume).filter(Resume.resume_id == resume_id_2).first()
            
            if not resume1 or not resume2:
                raise ValueError("One or both resumes not found")
            
            # Use WatsonX.ai to analyze differences
            comparison_prompt = f"""
            Compare these two resume versions and identify key differences:
            
            RESUME 1 (v{resume1.version}):
            {json.dumps(resume1.content, indent=2)}
            
            RESUME 2 (v{resume2.version}):
            {json.dumps(resume2.content, indent=2)}
            
            Provide comparison results in JSON format:
            {{
                "summary": "Brief summary of main differences",
                "sections_changed": ["section1", "section2"],
                "detailed_changes": [
                    {{
                        "section": "experience",
                        "change_type": "modified",
                        "before": "Original text",
                        "after": "Modified text",
                        "impact": "Positive/Negative/Neutral"
                    }}
                ],
                "score_comparison": {{
                    "resume1_score": 0.75,
                    "resume2_score": 0.85,
                    "improvement": 0.10
                }},
                "recommendations": [
                    "Keep the improved formatting from version 2",
                    "Consider combining strengths from both versions"
                ]
            }}
            """
            
            result = await self.watsonx_client.generate_text(comparison_prompt)
            
            if result["success"]:
                try:
                    comparison_data = json.loads(result["generated_text"])
                    
                    return AgentResponse(
                        success=True,
                        data={
                            "resume1": {
                                "resume_id": resume1.resume_id,
                                "version": resume1.version,
                                "title": resume1.title,
                                "ats_score": resume1.ats_score
                            },
                            "resume2": {
                                "resume_id": resume2.resume_id,
                                "version": resume2.version,
                                "title": resume2.title,
                                "ats_score": resume2.ats_score
                            },
                            "comparison": comparison_data
                        }
                    ).to_dict()
                    
                except json.JSONDecodeError:
                    # Fallback comparison
                    basic_comparison = await self._basic_resume_comparison(resume1, resume2)
                    
                    return AgentResponse(
                        success=True,
                        data=basic_comparison,
                        metadata={"comparison_method": "basic_fallback"}
                    ).to_dict()
            else:
                raise Exception("Failed to generate comparison")
                
        except Exception as e:
            logger.error(f"Error comparing resumes: {str(e)}")
            raise
    
    async def _calculate_acceptance_probability(self, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Calculate acceptance probability for resume-job matching
        
        Args:
            task_data: Task parameters including resume_id and job_id
            db: Database session
            
        Returns:
            Acceptance probability calculation
        """
        try:
            resume_id = task_data.get("resume_id")
            job_id = task_data.get("job_id")
            
            if not resume_id or not job_id:
                raise ValueError("Both resume_id and job_id are required")
            
            # Get resume and job
            resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
            job = db.query(Job).filter(Job.job_id == job_id).first()
            
            if not resume:
                raise ValueError(f"Resume not found: {resume_id}")
            if not job:
                raise ValueError(f"Job not found: {job_id}")
            
            # Calculate acceptance probability using AI
            probability_prompt = f"""
            Calculate the acceptance probability for this resume-job match:
            
            RESUME:
            - Title: {resume.title}
            - ATS Score: {resume.ats_score or 'N/A'}
            - Content: {json.dumps(resume.content, indent=2)[:1000]}...
            
            JOB:
            - Title: {job.title}
            - Company: {job.company}
            - Requirements: {job.requirements}
            - Qualifications: {job.qualifications}
            - Description: {job.description[:500] if job.description else 'N/A'}...
            
            Analyze and provide results in JSON format:
            {{
                "acceptance_probability": 0.75,
                "confidence_level": "High",
                "matching_factors": [
                    {{
                        "factor": "Skills Match",
                        "score": 0.8,
                        "weight": 0.3,
                        "details": "Strong alignment in technical skills"
                    }},
                    {{
                        "factor": "Experience Level",
                        "score": 0.7,
                        "weight": 0.25,
                        "details": "Experience level matches requirements"
                    }}
                ],
                "improvement_suggestions": [
                    "Add more specific industry keywords",
                    "Highlight relevant project experience"
                ],
                "risk_factors": [
                    "Missing certification mentioned in requirements"
                ],
                "overall_assessment": "Strong candidate with good probability of acceptance"
            }}
            """
            
            result = await self.watsonx_client.generate_text(probability_prompt)
            
            if result["success"]:
                try:
                    probability_data = json.loads(result["generated_text"])
                    
                    return AgentResponse(
                        success=True,
                        data={
                            "resume_id": resume_id,
                            "job_id": job_id,
                            "probability_analysis": probability_data,
                            "calculated_at": datetime.utcnow().isoformat()
                        }
                    ).to_dict()
                    
                except json.JSONDecodeError:
                    # Fallback calculation
                    basic_probability = await self._basic_acceptance_probability(resume, job)
                    
                    return AgentResponse(
                        success=True,
                        data=basic_probability,
                        metadata={"calculation_method": "basic_fallback"}
                    ).to_dict()
            else:
                raise Exception("Failed to calculate acceptance probability")
                
        except Exception as e:
            logger.error(f"Error calculating acceptance probability: {str(e)}")
            raise
    
    async def _basic_resume_comparison(self, resume1: Resume, resume2: Resume) -> Dict[str, Any]:
        """Basic fallback resume comparison"""
        comparison = {
            "resume1": {
                "resume_id": resume1.resume_id,
                "version": resume1.version,
                "title": resume1.title,
                "ats_score": resume1.ats_score,
                "created_at": resume1.created_at.isoformat() if resume1.created_at else datetime.utcnow().isoformat()
            },
            "resume2": {
                "resume_id": resume2.resume_id,
                "version": resume2.version,
                "title": resume2.title,
                "ats_score": resume2.ats_score,
                "created_at": resume2.created_at.isoformat() if resume2.created_at else datetime.utcnow().isoformat()
            },
            "comparison": {
                "summary": "Basic comparison between resume versions",
                "score_difference": (resume2.ats_score or 0) - (resume1.ats_score or 0),
                "version_difference": resume2.version - resume1.version,
                "recommendations": [
                    "Review both versions to identify best elements",
                    "Consider combining strengths from both resumes"
                ]
            }
        }
        
        return comparison
    
    async def _basic_acceptance_probability(self, resume: Resume, job: Job) -> Dict[str, Any]:
        """Basic fallback acceptance probability calculation"""
        # Simple scoring based on available data
        base_score = 0.5  # Base probability
        
        # Adjust based on ATS score
        if resume.ats_score:
            ats_adjustment = (resume.ats_score - 0.5) * 0.4
            base_score += ats_adjustment
        
        # Ensure probability is between 0 and 1
        probability = max(0.1, min(0.9, base_score))
        
        return {
            "resume_id": resume.resume_id,
            "job_id": job.job_id,
            "probability_analysis": {
                "acceptance_probability": probability,
                "confidence_level": "Medium",
                "matching_factors": [
                    {
                        "factor": "ATS Compatibility",
                        "score": resume.ats_score or 0.5,
                        "weight": 0.4,
                        "details": "Based on resume ATS score"
                    }
                ],
                "improvement_suggestions": [
                    "Optimize resume for better ATS compatibility",
                    "Tailor content to job requirements"
                ],
                "overall_assessment": f"Estimated {probability:.0%} probability based on available data"
            },
            "calculated_at": datetime.utcnow().isoformat()
        }    
    
# Abstract method implementations required by BaseAgent
    
    async def _process_request_impl(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementation of request processing for resume optimization
        """
        try:
            task_type = user_input.get("task_type", "optimize_resume")
            user_id = user_input.get("user_id") or context.get("user_id")
            
            if task_type == "optimize_resume":
                resume_content = user_input.get("resume_content", "")
                target_job_id = user_input.get("target_job_id")
                job_description = user_input.get("job_description", "")
                
                if not resume_content:
                    raise ValueError("resume_content is required for optimization")
                
                # Use existing optimization method
                optimization_result = await self.optimize_resume(
                    resume_content=resume_content,
                    target_job_description=job_description,
                    user_preferences=user_input.get("preferences", {})
                )
                
                return {
                    "success": True,
                    "data": optimization_result,
                    "recommendations": [
                        {
                            "type": "resume_improvement",
                            "description": "Resume optimized for target position",
                            "action": "review_changes",
                            "priority": "high"
                        }
                    ],
                    "metadata": {
                        "target_job_id": target_job_id,
                        "optimization_timestamp": datetime.utcnow().isoformat()
                    }
                }
            
            elif task_type == "analyze_ats_compatibility":
                resume_content = user_input.get("resume_content", "")
                job_description = user_input.get("job_description", "")
                
                ats_analysis = await self.analyze_ats_compatibility(resume_content, job_description)
                
                return {
                    "success": True,
                    "data": ats_analysis,
                    "recommendations": [
                        {
                            "type": "ats_optimization",
                            "description": f"ATS compatibility score: {ats_analysis.get('ats_score', 0)}%",
                            "action": "improve_ats_score",
                            "priority": "medium"
                        }
                    ],
                    "metadata": {
                        "analysis_timestamp": datetime.utcnow().isoformat()
                    }
                }
            
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
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
        Implementation of recommendations generation for resume optimization
        """
        try:
            recommendations = []
            
            # Generate resume improvement recommendations
            current_resume = user_profile.get("resume_content", "")
            target_role = user_profile.get("target_role", "")
            
            if current_resume:
                recommendations.append({
                    "type": "resume_review",
                    "description": "Review and optimize your resume for better ATS compatibility",
                    "action": "optimize_resume",
                    "priority": "high",
                    "metadata": {
                        "target_role": target_role,
                        "estimated_time": "30-60 minutes"
                    }
                })
            
            if target_role:
                recommendations.append({
                    "type": "role_specific_optimization",
                    "description": f"Tailor your resume specifically for {target_role} positions",
                    "action": "customize_for_role",
                    "priority": "high",
                    "metadata": {
                        "target_role": target_role
                    }
                })
            
            return recommendations
                
        except Exception as e:
            logger.error(f"Error in _get_recommendations_impl: {str(e)}")
            return []