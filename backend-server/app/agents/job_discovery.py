"""
Job Discovery Agent
Specialized AI agent for finding and recommending jobs
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import json

from app.agents.base import BaseAgent
from app.models.job import Job, JobRecommendation
from app.models.user import UserProfile
from app.core.database import get_database
from app.integrations.watsonx import WatsonXClient

logger = logging.getLogger(__name__)


class JobDiscoveryAgent(BaseAgent):
    """
    AI agent specialized in job discovery and recommendation
    """
    
    def __init__(self, watsonx_client: WatsonXClient):
        super().__init__(
            agent_id="job_discovery_agent",
            watsonx_client=watsonx_client
        )
        self.watsonx_client = watsonx_client
        self.job_connectors = {}
    
    async def process_request(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user request for job discovery tasks
        
        Args:
            user_input: User request data
            context: Current conversation/session context
            
        Returns:
            Structured response with job recommendations and data
        """
        try:
            task_type = user_input.get("task_type", "recommend_jobs")
            user_id = user_input.get("user_id")
            
            if not user_id:
                raise ValueError("user_id is required for job discovery requests")
            
            # Process the task using existing task processing logic
            return await self.process_task(user_input)
            
        except Exception as e:
            logger.error(f"Error processing job discovery request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_recommendations(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate personalized job recommendations based on user profile
        
        Args:
            user_profile: User profile data
            
        Returns:
            List of personalized job recommendations
        """
        try:
            # Convert dict to UserProfile object if needed
            if isinstance(user_profile, dict):
                user_id = user_profile.get("user_id")
            else:
                user_id = user_profile.user_id
            
            task_data = {
                "task_type": "recommend_jobs",
                "user_id": user_id,
                "limit": 10
            }
            
            result = await self.process_task(task_data)
            
            if result.get("success"):
                return result.get("recommendations", [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return []
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process job discovery tasks
        
        Args:
            task_data: Task information including user_id and task type
            
        Returns:
            Task processing results
        """
        try:
            task_type = task_data.get("task_type")
            user_id = task_data.get("user_id")
            
            if not user_id:
                raise ValueError("user_id is required for job discovery tasks")
            
            # Get user profile
            db = next(get_database())
            user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if not user_profile:
                raise ValueError(f"User profile not found for user_id: {user_id}")
            
            if task_type == "discover_jobs":
                return await self._discover_jobs(user_profile, task_data, db)
            elif task_type == "recommend_jobs":
                return await self._recommend_jobs(user_profile, task_data, db)
            elif task_type == "analyze_job_market":
                return await self._analyze_job_market(user_profile, task_data, db)
            elif task_type == "score_job_compatibility":
                return await self._score_job_compatibility(user_profile, task_data, db)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
        except Exception as e:
            logger.error(f"Error processing job discovery task: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _discover_jobs(self, user_profile: UserProfile, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Discover new job opportunities for the user
        
        Args:
            user_profile: User profile data
            task_data: Task parameters
            db: Database session
            
        Returns:
            Discovered jobs results
        """
        try:
            search_params = task_data.get("search_params", {})
            
            # Extract search criteria from user profile and task data
            search_criteria = self._build_search_criteria(user_profile, search_params)
            
            # Search jobs from multiple sources
            discovered_jobs = []
            
            # Search from each configured job board
            for source, connector in self.job_connectors.items():
                try:
                    jobs = await connector.search_jobs(search_criteria)
                    discovered_jobs.extend(jobs)
                    logger.info(f"Found {len(jobs)} jobs from {source}")
                except Exception as e:
                    logger.error(f"Error searching jobs from {source}: {str(e)}")
            
            # Store new jobs in database
            new_jobs_count = 0
            for job_data in discovered_jobs:
                if not db.query(Job).filter(
                    Job.external_id == job_data.get("external_id"),
                    Job.source == job_data.get("source")
                ).first():
                    job = Job(
                        job_id=str(uuid.uuid4()),
                        **job_data
                    )
                    db.add(job)
                    new_jobs_count += 1
            
            db.commit()
            
            return {
                "success": True,
                "jobs_discovered": len(discovered_jobs),
                "new_jobs_stored": new_jobs_count,
                "search_criteria": search_criteria,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in job discovery: {str(e)}")
            raise
    
    async def _recommend_jobs(self, user_profile: UserProfile, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Generate personalized job recommendations
        
        Args:
            user_profile: User profile data
            task_data: Task parameters
            db: Database session
            
        Returns:
            Job recommendations results
        """
        try:
            limit = task_data.get("limit", 10)
            
            # Get recent jobs that haven't been recommended to this user
            recent_jobs = db.query(Job).filter(
                Job.is_active == True,
                Job.scraped_at >= datetime.utcnow() - timedelta(days=30)
            ).limit(100).all()
            
            recommendations = []
            
            for job in recent_jobs:
                # Check if already recommended
                existing_rec = db.query(JobRecommendation).filter(
                    JobRecommendation.user_id == user_profile.user_id,
                    JobRecommendation.job_id == job.job_id
                ).first()
                
                if existing_rec:
                    continue
                
                # Score job compatibility
                compatibility_result = await self._calculate_compatibility_score(user_profile, job)
                
                if compatibility_result["compatibility_score"] >= 0.5:  # Lowered threshold for better coverage
                    recommendation = JobRecommendation(
                        user_id=user_profile.user_id,
                        job_id=job.job_id,
                        compatibility_score=compatibility_result["compatibility_score"],
                        reasoning=compatibility_result["reasoning"],
                        skill_match_score=compatibility_result.get("skill_match_score", 0.0),
                        experience_match_score=compatibility_result.get("experience_match_score", 0.0),
                        location_match_score=compatibility_result.get("location_match_score", 0.0),
                        salary_match_score=compatibility_result.get("salary_match_score", 0.0),
                        agent_id=self.agent_id,
                        recommendation_context={
                            "career_growth_score": compatibility_result.get("career_growth_score", 0.0),
                            "strengths": compatibility_result.get("strengths", []),
                            "concerns": compatibility_result.get("concerns", []),
                            "recommendation": compatibility_result.get("recommendation", "")
                        }
                    )
                    
                    db.add(recommendation)
                    recommendations.append({
                        "job": job.to_dict(),
                        "compatibility_score": compatibility_result["compatibility_score"],
                        "reasoning": compatibility_result["reasoning"]
                    })
                
                if len(recommendations) >= limit:
                    break
            
            db.commit()
            
            # Sort by compatibility score
            recommendations.sort(key=lambda x: x["compatibility_score"], reverse=True)
            
            return {
                "success": True,
                "recommendations": recommendations,
                "total_recommended": len(recommendations),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating job recommendations: {str(e)}")
            raise
    
    async def _analyze_job_market(self, user_profile: UserProfile, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Analyze job market trends for the user's field
        
        Args:
            user_profile: User profile data
            task_data: Task parameters
            db: Database session
            
        Returns:
            Market analysis results
        """
        try:
            # Get jobs in user's industry/field
            user_skills = user_profile.skills or []
            user_industry = user_profile.industry
            
            # Query relevant jobs
            query = db.query(Job).filter(Job.is_active == True)
            
            if user_industry:
                query = query.filter(Job.industry == user_industry)
            
            recent_jobs = query.filter(
                Job.scraped_at >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            # Analyze market trends using WatsonX.ai
            market_analysis_prompt = f"""
            Analyze the job market based on the following data:
            
            User Profile:
            - Industry: {user_industry}
            - Skills: {[skill.get('name', '') for skill in user_skills if isinstance(skill, dict)]}
            - Experience Level: {user_profile.years_experience} years
            
            Recent Job Postings: {len(recent_jobs)} jobs
            
            Provide analysis on:
            1. Market demand for user's skills
            2. Salary trends in the industry
            3. Most in-demand skills
            4. Geographic hotspots
            5. Career growth opportunities
            
            Format as JSON with clear insights.
            """
            
            analysis_result = await self.watsonx_client.generate_text(market_analysis_prompt)
            
            if analysis_result["success"]:
                try:
                    market_insights = json.loads(analysis_result["generated_text"])
                except json.JSONDecodeError:
                    market_insights = {"analysis": analysis_result["generated_text"]}
            else:
                market_insights = {"error": "Failed to generate market analysis"}
            
            return {
                "success": True,
                "market_analysis": market_insights,
                "jobs_analyzed": len(recent_jobs),
                "analysis_date": datetime.utcnow().isoformat(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing job market: {str(e)}")
            raise
    
    async def _score_job_compatibility(self, user_profile: UserProfile, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Score compatibility between user and specific job
        
        Args:
            user_profile: User profile data
            task_data: Task parameters including job_id
            db: Database session
            
        Returns:
            Compatibility scoring results
        """
        try:
            job_id = task_data.get("job_id")
            if not job_id:
                raise ValueError("job_id is required for compatibility scoring")
            
            job = db.query(Job).filter(Job.job_id == job_id).first()
            if not job:
                raise ValueError(f"Job not found: {job_id}")
            
            compatibility_result = await self._calculate_compatibility_score(user_profile, job)
            
            return {
                "success": True,
                "job_id": job_id,
                "compatibility_score": compatibility_result["compatibility_score"],
                "detailed_scores": {
                    "skill_match": compatibility_result.get("skill_match_score", 0.0),
                    "experience_match": compatibility_result.get("experience_match_score", 0.0),
                    "location_match": compatibility_result.get("location_match_score", 0.0),
                    "salary_match": compatibility_result.get("salary_match_score", 0.0)
                },
                "reasoning": compatibility_result["reasoning"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scoring job compatibility: {str(e)}")
            raise
    
    async def _calculate_compatibility_score(self, user_profile: UserProfile, job: Job) -> Dict[str, Any]:
        """
        Calculate compatibility score between user and job using enhanced AI analysis
        
        Args:
            user_profile: User profile data
            job: Job data
            
        Returns:
            Compatibility analysis with score and reasoning
        """
        try:
            # Prepare user profile summary
            user_skills = [skill.get('name', '') for skill in (user_profile.skills or []) if isinstance(skill, dict)]
            user_experience = user_profile.experience or []
            
            # Calculate basic compatibility scores first
            skill_match = self._calculate_skill_match(user_profile, job)
            experience_match = self._calculate_experience_match(user_profile, job)
            location_match = self._calculate_location_match(user_profile, job)
            salary_match = self._calculate_salary_match(user_profile, job)
            
            # Enhanced AI analysis prompt
            compatibility_prompt = f"""
            Analyze the compatibility between this user profile and job posting. Use the pre-calculated scores as a baseline and provide enhanced analysis:
            
            USER PROFILE:
            - Name: {user_profile.first_name} {user_profile.last_name}
            - Current Title: {user_profile.current_title}
            - Years Experience: {user_profile.years_experience}
            - Industry: {user_profile.industry}
            - Location: {user_profile.location}
            - Skills: {user_skills}
            - Career Goals: {user_profile.career_goals}
            - Job Preferences: {user_profile.job_preferences}
            
            JOB POSTING:
            - Title: {job.title}
            - Company: {job.company}
            - Location: {job.location}
            - Remote Type: {job.remote_type}
            - Experience Level: {job.experience_level}
            - Employment Type: {job.employment_type}
            - Industry: {job.industry}
            - Requirements: {job.requirements}
            - Qualifications: {job.qualifications}
            - Salary Range: ${job.salary_min} - ${job.salary_max} {job.salary_currency}
            - Description: {job.description[:800] if job.description else 'No description available'}
            
            PRE-CALCULATED SCORES:
            - Skill Match: {skill_match:.2f}
            - Experience Match: {experience_match:.2f}
            - Location Match: {location_match:.2f}
            - Salary Match: {salary_match:.2f}
            
            Provide an enhanced compatibility analysis considering:
            1. Technical skill alignment and transferable skills
            2. Career progression and growth potential
            3. Company culture fit based on user preferences
            4. Industry transition feasibility
            5. Role responsibilities alignment with career goals
            
            Calculate an overall compatibility score (0.0 to 1.0) that weighs:
            - Skills (40%)
            - Experience (25%)
            - Location/Remote (15%)
            - Salary (10%)
            - Career Growth (10%)
            
            Format as JSON:
            {{
                "compatibility_score": 0.85,
                "skill_match_score": 0.9,
                "experience_match_score": 0.8,
                "location_match_score": 1.0,
                "salary_match_score": 0.7,
                "career_growth_score": 0.9,
                "reasoning": "Detailed explanation covering skill alignment, career fit, and growth potential...",
                "strengths": ["Strong technical skill match", "Good career progression opportunity"],
                "concerns": ["Salary slightly below expectations", "Location requires relocation"],
                "recommendation": "Highly recommended - excellent skill match with strong growth potential"
            }}
            """
            
            result = await self.watsonx_client.generate_text(compatibility_prompt)
            
            if result["success"]:
                try:
                    compatibility_data = json.loads(result["generated_text"])
                    
                    # Ensure all required fields are present with fallbacks
                    compatibility_data.setdefault("compatibility_score", (skill_match * 0.4 + experience_match * 0.25 + location_match * 0.15 + salary_match * 0.1 + 0.8 * 0.1))
                    compatibility_data.setdefault("skill_match_score", skill_match)
                    compatibility_data.setdefault("experience_match_score", experience_match)
                    compatibility_data.setdefault("location_match_score", location_match)
                    compatibility_data.setdefault("salary_match_score", salary_match)
                    compatibility_data.setdefault("career_growth_score", 0.7)
                    compatibility_data.setdefault("strengths", [])
                    compatibility_data.setdefault("concerns", [])
                    compatibility_data.setdefault("recommendation", "Consider this opportunity")
                    
                    return compatibility_data
                    
                except json.JSONDecodeError:
                    # Fallback to calculated scores if JSON parsing fails
                    overall_score = skill_match * 0.4 + experience_match * 0.25 + location_match * 0.15 + salary_match * 0.1 + 0.7 * 0.1
                    return {
                        "compatibility_score": overall_score,
                        "skill_match_score": skill_match,
                        "experience_match_score": experience_match,
                        "location_match_score": location_match,
                        "salary_match_score": salary_match,
                        "career_growth_score": 0.7,
                        "reasoning": result["generated_text"],
                        "strengths": [],
                        "concerns": [],
                        "recommendation": "Review this opportunity"
                    }
            else:
                # Fallback to calculated scores
                overall_score = skill_match * 0.4 + experience_match * 0.25 + location_match * 0.15 + salary_match * 0.1 + 0.5 * 0.1
                return {
                    "compatibility_score": overall_score,
                    "skill_match_score": skill_match,
                    "experience_match_score": experience_match,
                    "location_match_score": location_match,
                    "salary_match_score": salary_match,
                    "career_growth_score": 0.5,
                    "reasoning": "Unable to generate detailed AI analysis, using calculated scores",
                    "strengths": [],
                    "concerns": [],
                    "recommendation": "Review this opportunity"
                }
                
        except Exception as e:
            logger.error(f"Error calculating compatibility score: {str(e)}")
            return {
                "compatibility_score": 0.0,
                "skill_match_score": 0.0,
                "experience_match_score": 0.0,
                "location_match_score": 0.0,
                "salary_match_score": 0.0,
                "career_growth_score": 0.0,
                "reasoning": f"Error in compatibility analysis: {str(e)}",
                "strengths": [],
                "concerns": [],
                "recommendation": "Unable to analyze"
            }
    
    def _calculate_skill_match(self, user_profile: UserProfile, job: Job) -> float:
        """
        Calculate skill match score between user and job
        
        Args:
            user_profile: User profile data
            job: Job data
            
        Returns:
            Skill match score (0.0 to 1.0)
        """
        try:
            user_skills = [skill.get('name', '').lower() for skill in (user_profile.skills or []) if isinstance(skill, dict)]
            job_requirements = job.requirements or []
            job_qualifications = job.qualifications or []
            
            # Combine job requirements and qualifications
            required_skills = []
            for req in job_requirements:
                if isinstance(req, str):
                    required_skills.append(req.lower())
            for qual in job_qualifications:
                if isinstance(qual, str):
                    required_skills.append(qual.lower())
            
            if not required_skills or not user_skills:
                return 0.5  # Neutral score if no skills data
            
            # Calculate exact matches
            exact_matches = 0
            for req_skill in required_skills:
                for user_skill in user_skills:
                    if user_skill in req_skill or req_skill in user_skill:
                        exact_matches += 1
                        break
            
            # Calculate skill match percentage
            skill_match = min(exact_matches / len(required_skills), 1.0)
            
            # Boost score if user has more skills than required
            if len(user_skills) > len(required_skills):
                skill_match = min(skill_match * 1.1, 1.0)
            
            return skill_match
            
        except Exception as e:
            logger.error(f"Error calculating skill match: {str(e)}")
            return 0.3
    
    def _calculate_experience_match(self, user_profile: UserProfile, job: Job) -> float:
        """
        Calculate experience match score between user and job
        
        Args:
            user_profile: User profile data
            job: Job data
            
        Returns:
            Experience match score (0.0 to 1.0)
        """
        try:
            user_years = user_profile.years_experience or 0
            job_level = job.experience_level or 'mid'
            
            # Define experience level ranges
            level_ranges = {
                'entry': (0, 2),
                'mid': (2, 5),
                'senior': (5, 10),
                'executive': (10, 20),
                'lead': (7, 15)
            }
            
            if job_level not in level_ranges:
                return 0.7  # Neutral score for unknown levels
            
            min_exp, max_exp = level_ranges[job_level]
            
            if min_exp <= user_years <= max_exp:
                return 1.0  # Perfect match
            elif user_years < min_exp:
                # Under-qualified, score based on how close
                gap = min_exp - user_years
                return max(0.3, 1.0 - (gap * 0.2))
            else:
                # Over-qualified, slight penalty but still good
                excess = user_years - max_exp
                return max(0.7, 1.0 - (excess * 0.05))
                
        except Exception as e:
            logger.error(f"Error calculating experience match: {str(e)}")
            return 0.5
    
    def _calculate_location_match(self, user_profile: UserProfile, job: Job) -> float:
        """
        Calculate location match score between user and job
        
        Args:
            user_profile: User profile data
            job: Job data
            
        Returns:
            Location match score (0.0 to 1.0)
        """
        try:
            user_location = (user_profile.location or '').lower()
            job_location = (job.location or '').lower()
            remote_type = (job.remote_type or '').lower()
            
            # Remote work gets high score
            if remote_type in ['remote', 'fully remote']:
                return 1.0
            
            # Hybrid work gets good score
            if remote_type in ['hybrid', 'flexible']:
                return 0.8
            
            # Check location match
            if not user_location or not job_location:
                return 0.5  # Neutral if location data missing
            
            # Exact location match
            if user_location in job_location or job_location in user_location:
                return 1.0
            
            # Same city/state match (basic check)
            user_parts = user_location.split(',')
            job_parts = job_location.split(',')
            
            for user_part in user_parts:
                for job_part in job_parts:
                    if user_part.strip() in job_part.strip() or job_part.strip() in user_part.strip():
                        return 0.8
            
            # No match, but onsite work
            return 0.3
            
        except Exception as e:
            logger.error(f"Error calculating location match: {str(e)}")
            return 0.5
    
    def _calculate_salary_match(self, user_profile: UserProfile, job: Job) -> float:
        """
        Calculate salary match score between user preferences and job offer
        
        Args:
            user_profile: User profile data
            job: Job data
            
        Returns:
            Salary match score (0.0 to 1.0)
        """
        try:
            job_preferences = user_profile.job_preferences or {}
            if not isinstance(job_preferences, dict):
                return 0.7  # Neutral if no preferences
            
            desired_salary = job_preferences.get('salary_min')
            if not desired_salary:
                return 0.7  # Neutral if no salary preference
            
            job_min = job.salary_min
            job_max = job.salary_max
            
            if not job_min and not job_max:
                return 0.5  # Neutral if no salary info
            
            # Use job_max if available, otherwise job_min
            job_salary = job_max or job_min
            
            if job_salary >= desired_salary:
                # Salary meets or exceeds expectations
                excess_ratio = (job_salary - desired_salary) / desired_salary
                return min(1.0, 0.8 + excess_ratio * 0.2)
            else:
                # Salary below expectations
                shortfall_ratio = (desired_salary - job_salary) / desired_salary
                return max(0.2, 0.8 - shortfall_ratio * 0.6)
                
        except Exception as e:
            logger.error(f"Error calculating salary match: {str(e)}")
            return 0.5

    def _build_search_criteria(self, user_profile: UserProfile, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build job search criteria from user profile and parameters
        
        Args:
            user_profile: User profile data
            search_params: Additional search parameters
            
        Returns:
            Search criteria dictionary
        """
        criteria = {
            "keywords": [],
            "location": user_profile.location,
            "remote_type": None,
            "experience_level": None,
            "industry": user_profile.industry,
            "salary_min": None,
            "employment_type": "full-time"
        }
        
        # Add skills as keywords
        if user_profile.skills:
            criteria["keywords"].extend([
                skill.get('name', '') for skill in user_profile.skills 
                if isinstance(skill, dict) and skill.get('name')
            ])
        
        # Add current title as keyword
        if user_profile.current_title:
            criteria["keywords"].append(user_profile.current_title)
        
        # Determine experience level
        years_exp = user_profile.years_experience or 0
        if years_exp < 2:
            criteria["experience_level"] = "entry"
        elif years_exp < 5:
            criteria["experience_level"] = "mid"
        elif years_exp < 10:
            criteria["experience_level"] = "senior"
        else:
            criteria["experience_level"] = "executive"
        
        # Apply job preferences if available
        if user_profile.job_preferences:
            prefs = user_profile.job_preferences
            if isinstance(prefs, dict):
                criteria["salary_min"] = prefs.get("salary_min")
                criteria["remote_type"] = prefs.get("work_arrangement")
                if prefs.get("employment_type"):
                    criteria["employment_type"] = prefs["employment_type"][0] if prefs["employment_type"] else "full-time"
        
        # Override with explicit search parameters
        criteria.update(search_params)
        
        return criteria
    
    def register_job_connector(self, source: str, connector):
        """
        Register a job board connector
        
        Args:
            source: Job board source name
            connector: Job board connector instance
        """
        self.job_connectors[source] = connector
        logger.info(f"Registered job connector for {source}")
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get agent status information
        
        Returns:
            Agent status dictionary
        """
        status = await super().get_status()
        status.update({
            "job_connectors": list(self.job_connectors.keys()),
            "total_connectors": len(self.job_connectors)
        })
        return status    

    # Abstract method implementations required by BaseAgent
    
    async def _process_request_impl(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementation of request processing for job discovery
        """
        try:
            task_type = user_input.get("task_type", "search_jobs")
            user_id = user_input.get("user_id") or context.get("user_id")
            
            # Process the request using existing methods
            if task_type == "search_jobs":
                search_params = {
                    "keywords": user_input.get("keywords", ""),
                    "location": user_input.get("location", ""),
                    "experience_level": user_input.get("experience_level", ""),
                    "job_type": user_input.get("job_type", ""),
                    "salary_min": user_input.get("salary_min"),
                    "salary_max": user_input.get("salary_max"),
                    "remote_ok": user_input.get("remote_ok", False)
                }
                
                jobs = await self.search_jobs(search_params)
                
                return {
                    "success": True,
                    "data": {"jobs": jobs},
                    "recommendations": [
                        {
                            "type": "job_match",
                            "description": f"Found {len(jobs)} job opportunities matching your criteria",
                            "action": "review_jobs",
                            "priority": "high"
                        }
                    ],
                    "metadata": {
                        "search_params": search_params,
                        "results_count": len(jobs),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            
            elif task_type == "get_recommendations":
                user_profile = user_input.get("user_profile", {})
                recommendations = await self.get_recommendations(user_profile)
                
                return {
                    "success": True,
                    "data": {"recommendations": recommendations},
                    "recommendations": recommendations,
                    "metadata": {
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
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
        Implementation of recommendations generation for job discovery
        """
        try:
            # Use existing get_recommendations method
            recommendations = await self.get_recommendations(user_profile)
            return recommendations
                
        except Exception as e:
            logger.error(f"Error in _get_recommendations_impl: {str(e)}")
            return []