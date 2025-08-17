"""
Career Strategy Agent
Specialized AI agent for career roadmap generation, goal setting, and progress tracking
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
from app.models.career_strategy import (
    CareerRoadmap, CareerGoal, CareerMilestone, ProgressTracking,
    GoalStatus, MilestoneType,
    CareerRoadmapCreate, CareerGoalCreate, CareerMilestoneCreate,
    CareerRoadmapResponse, CareerGoalResponse, CareerMilestoneResponse
)
from app.core.database import get_database
from app.integrations.watsonx import WatsonXClient
from app.integrations.langchain_utils import LangChainAgentManager

logger = logging.getLogger(__name__)


class CareerStrategyAgent(BaseAgent):
    """
    AI agent specialized in career strategy development, roadmap generation, and progress tracking
    """
    
    def __init__(self, watsonx_client: WatsonXClient, langchain_manager: LangChainAgentManager = None):
        super().__init__(
            agent_id="career_strategy_agent",
            watsonx_client=watsonx_client
        )
        self.watsonx_client = watsonx_client
        self.langchain_manager = langchain_manager
        
        # Career development frameworks and methodologies
        self.career_frameworks = {
            "skill_based": "Focus on developing specific technical and soft skills",
            "experience_based": "Gain experience through projects and roles",
            "network_based": "Build professional network and relationships",
            "education_based": "Pursue formal education and certifications",
            "hybrid": "Combination of multiple approaches"
        }
        
        # Common career transition patterns
        self.transition_patterns = {
            "vertical": "Moving up in the same field/function",
            "horizontal": "Moving to similar role in different industry",
            "diagonal": "Moving to different role in same industry",
            "pivot": "Complete career change to new field"
        }
    
    async def process_request(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user request for career strategy tasks
        """
        try:
            task_type = user_input.get("task_type", "generate_roadmap")
            user_id = user_input.get("user_id")
            
            if not user_id:
                raise ValueError("user_id is required for career strategy requests")
            
            result = await self.process_task(user_input)
            
            return AgentResponse(
                success=result.get("success", False),
                data=result.get("data"),
                error=result.get("error"),
                recommendations=result.get("recommendations", []),
                metadata=result.get("metadata", {})
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Error processing career strategy request: {str(e)}")
            return AgentResponse(
                success=False,
                error=str(e)
            ).to_dict()
    
    async def get_recommendations(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate personalized career strategy recommendations
        """
        try:
            user_id = user_profile.get("user_id") if isinstance(user_profile, dict) else user_profile.user_id
            
            task_data = {
                "task_type": "generate_career_recommendations",
                "user_id": user_id
            }
            
            result = await self.process_task(task_data)
            
            if result.get("success"):
                return result.get("recommendations", [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting career strategy recommendations: {str(e)}")
            return []
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process career strategy tasks
        """
        try:
            task_type = task_data.get("task_type")
            user_id = task_data.get("user_id")
            
            if not user_id:
                raise ValueError("user_id is required for career strategy tasks")
            
            # Create mock user profile for testing
            mock_user_profile = type('MockUserProfile', (), {
                'user_id': user_id,
                'skills': [],
                'experience': [],
                'career_goals': {},
                'years_experience': 5,
                'industry': 'Technology',
                'current_role': 'Software Developer',
                'education': [],
                'certifications': [],
                'updated_at': datetime.utcnow()
            })()
            
            # Mock database
            class MockDB:
                def add(self, obj): pass
                def commit(self): pass
                def query(self, model): 
                    return type('MockQuery', (), {
                        'filter': lambda *args: type('MockFilter', (), {
                            'first': lambda: None,
                            'all': lambda: []
                        })()
                    })()
            
            db = MockDB()
            
            if task_type == "generate_roadmap":
                return await self._generate_career_roadmap(mock_user_profile, task_data, db)
            elif task_type == "create_goals":
                return await self._create_career_goals(mock_user_profile, task_data, db)
            elif task_type == "track_progress":
                return await self._track_progress(mock_user_profile, task_data, db)
            elif task_type == "update_roadmap":
                return await self._update_roadmap(mock_user_profile, task_data, db)
            elif task_type == "analyze_market_trends":
                return await self._analyze_market_trends(task_data, db)
            elif task_type == "generate_career_recommendations":
                return await self._generate_career_recommendations(mock_user_profile, task_data, db)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
        except Exception as e:
            logger.error(f"Error processing career strategy task: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _generate_career_roadmap(self, user_profile, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Generate comprehensive career roadmap based on current and target roles
        """
        try:
            current_role = task_data.get("current_role", user_profile.current_role)
            target_role = task_data.get("target_role", "")
            target_industry = task_data.get("target_industry", user_profile.industry)
            timeline_months = task_data.get("timeline_months", 24)
            target_company = task_data.get("target_company", "")
            
            if not target_role:
                raise ValueError("target_role is required for roadmap generation")
            
            # Use WatsonX.ai to generate comprehensive career roadmap
            roadmap_prompt = f"""
            Create a comprehensive career roadmap for transitioning from {current_role} to {target_role}.
            
            User Profile:
            - Current Role: {current_role}
            - Target Role: {target_role}
            - Industry: {target_industry}
            - Years Experience: {user_profile.years_experience}
            - Current Skills: {json.dumps(user_profile.skills, indent=2)}
            - Timeline: {timeline_months} months
            - Target Company: {target_company or "Any suitable company"}
            
            Generate a detailed roadmap including:
            1. Career transition strategy and approach
            2. Key milestones with specific timelines
            3. Skills to develop and certifications to obtain
            4. Experience requirements and how to gain them
            5. Networking strategies and target connections
            6. Potential challenges and mitigation strategies
            7. Success metrics and progress indicators
            
            Return in JSON format:
            {{
                "roadmap": {{
                    "title": "Career Transition: {current_role} to {target_role}",
                    "description": "Comprehensive roadmap for career advancement",
                    "transition_type": "vertical|horizontal|diagonal|pivot",
                    "difficulty_level": "low|medium|high",
                    "success_probability": 85,
                    "key_strategies": ["strategy1", "strategy2"],
                    "timeline_breakdown": {{
                        "phase1": {{"months": "1-6", "focus": "Foundation building"}},
                        "phase2": {{"months": "7-12", "focus": "Skill development"}},
                        "phase3": {{"months": "13-18", "focus": "Experience gaining"}},
                        "phase4": {{"months": "19-24", "focus": "Job search and transition"}}
                    }}
                }},
                "milestones": [
                    {{
                        "title": "Complete Cloud Certification",
                        "type": "certification",
                        "timeline": "Month 3",
                        "priority": "high",
                        "description": "Obtain AWS Solutions Architect certification",
                        "requirements": ["Study materials", "Practice exams", "Hands-on experience"],
                        "success_metrics": ["Pass certification exam", "Score above 80%"],
                        "estimated_effort": "40 hours"
                    }}
                ],
                "goals": [
                    {{
                        "title": "Develop Leadership Skills",
                        "category": "soft_skills",
                        "priority": 1,
                        "timeline": "6 months",
                        "description": "Build leadership capabilities for senior role",
                        "success_criteria": ["Lead a team project", "Complete leadership training", "Get 360 feedback"],
                        "resources_needed": ["Leadership course", "Mentorship", "Team project opportunity"]
                    }}
                ],
                "skill_development_plan": {{
                    "technical_skills": [
                        {{"skill": "Kubernetes", "current_level": "none", "target_level": "intermediate", "timeline": "4 months"}},
                        {{"skill": "System Design", "current_level": "basic", "target_level": "advanced", "timeline": "6 months"}}
                    ],
                    "soft_skills": [
                        {{"skill": "Leadership", "current_level": "basic", "target_level": "intermediate", "timeline": "6 months"}},
                        {{"skill": "Strategic Thinking", "current_level": "basic", "target_level": "advanced", "timeline": "8 months"}}
                    ]
                }},
                "networking_strategy": {{
                    "target_connections": 50,
                    "key_personas": ["Senior Engineers", "Engineering Managers", "CTOs"],
                    "networking_channels": ["LinkedIn", "Tech conferences", "Meetups", "Internal networking"],
                    "monthly_goals": {{"new_connections": 5, "meaningful_conversations": 10}}
                }},
                "experience_requirements": [
                    {{"type": "project_leadership", "description": "Lead a cross-functional project", "timeline": "Month 8"}},
                    {{"type": "mentoring", "description": "Mentor junior developers", "timeline": "Month 6"}},
                    {{"type": "architecture_design", "description": "Design system architecture", "timeline": "Month 10"}}
                ],
                "potential_challenges": [
                    {{"challenge": "Limited leadership experience", "mitigation": "Seek stretch assignments and mentorship", "probability": "high"}},
                    {{"challenge": "Technical skill gaps", "mitigation": "Structured learning plan and hands-on practice", "probability": "medium"}}
                ],
                "success_metrics": {{
                    "quarterly_reviews": true,
                    "skill_assessments": true,
                    "network_growth": true,
                    "project_outcomes": true,
                    "interview_readiness": true
                }}
            }}
            """
            
            result = await self.watsonx_client.generate_text(roadmap_prompt)
            
            if result["success"]:
                try:
                    roadmap_data = json.loads(result["generated_text"])
                    
                    # Create roadmap ID and enhance data
                    roadmap_id = str(uuid.uuid4())
                    roadmap_data["roadmap"]["roadmap_id"] = roadmap_id
                    roadmap_data["roadmap"]["user_id"] = user_profile.user_id
                    roadmap_data["roadmap"]["created_at"] = datetime.utcnow().isoformat()
                    
                    # Add IDs to milestones and goals
                    for milestone in roadmap_data.get("milestones", []):
                        milestone["milestone_id"] = str(uuid.uuid4())
                        milestone["roadmap_id"] = roadmap_id
                        milestone["user_id"] = user_profile.user_id
                    
                    for goal in roadmap_data.get("goals", []):
                        goal["goal_id"] = str(uuid.uuid4())
                        goal["roadmap_id"] = roadmap_id
                        goal["user_id"] = user_profile.user_id
                    
                    # Generate recommendations based on roadmap
                    recommendations = self._generate_roadmap_recommendations(roadmap_data)
                    
                    return {
                        "success": True,
                        "data": roadmap_data,
                        "recommendations": recommendations,
                        "metadata": {
                            "roadmap_id": roadmap_id,
                            "generation_method": "watsonx_ai",
                            "timeline_months": timeline_months,
                            "transition_type": roadmap_data["roadmap"].get("transition_type", "unknown")
                        }
                    }
                    
                except json.JSONDecodeError:
                    # Fallback to basic roadmap generation
                    return await self._basic_roadmap_generation(current_role, target_role, timeline_months, user_profile)
            else:
                # Fallback to basic roadmap generation
                return await self._basic_roadmap_generation(current_role, target_role, timeline_months, user_profile)
                
        except Exception as e:
            logger.error(f"Error generating career roadmap: {str(e)}")
            raise
    
    async def _create_career_goals(self, user_profile, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Create specific career goals based on roadmap or user input
        """
        try:
            roadmap_id = task_data.get("roadmap_id")
            goal_categories = task_data.get("categories", ["skill_development", "experience", "networking"])
            timeline_months = task_data.get("timeline_months", 12)
            
            # Generate goals using WatsonX.ai
            goals_prompt = f"""
            Create specific, measurable career goals for the user based on their profile and objectives.
            
            User Profile:
            - Current Role: {user_profile.current_role}
            - Years Experience: {user_profile.years_experience}
            - Industry: {user_profile.industry}
            - Current Skills: {json.dumps(user_profile.skills, indent=2)}
            
            Goal Categories: {goal_categories}
            Timeline: {timeline_months} months
            Roadmap ID: {roadmap_id}
            
            Create SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound) for each category.
            
            Return in JSON format:
            {{
                "goals": [
                    {{
                        "title": "Master Kubernetes Container Orchestration",
                        "description": "Develop advanced Kubernetes skills for container orchestration and management",
                        "category": "skill_development",
                        "priority": 1,
                        "timeline_months": 4,
                        "success_criteria": [
                            "Complete Kubernetes certification (CKA)",
                            "Deploy and manage 3 production applications",
                            "Troubleshoot complex cluster issues"
                        ],
                        "resources_needed": [
                            "Kubernetes course subscription",
                            "Practice cluster environment",
                            "Certification exam fee"
                        ],
                        "dependencies": ["Basic Docker knowledge", "Linux administration skills"],
                        "milestones": [
                            {{"title": "Complete basic Kubernetes course", "timeline": "Month 1"}},
                            {{"title": "Set up practice cluster", "timeline": "Month 2"}},
                            {{"title": "Deploy first application", "timeline": "Month 3"}},
                            {{"title": "Pass CKA certification", "timeline": "Month 4"}}
                        ]
                    }}
                ],
                "goal_summary": {{
                    "total_goals": 5,
                    "by_category": {{"skill_development": 2, "experience": 2, "networking": 1}},
                    "by_priority": {{"high": 2, "medium": 2, "low": 1}},
                    "estimated_total_effort": "200 hours",
                    "success_probability": 85
                }}
            }}
            """
            
            result = await self.watsonx_client.generate_text(goals_prompt)
            
            if result["success"]:
                try:
                    goals_data = json.loads(result["generated_text"])
                    
                    # Add IDs and metadata to goals
                    for goal in goals_data.get("goals", []):
                        goal["goal_id"] = str(uuid.uuid4())
                        goal["roadmap_id"] = roadmap_id
                        goal["user_id"] = user_profile.user_id
                        goal["status"] = GoalStatus.NOT_STARTED
                        goal["progress_percentage"] = 0.0
                        goal["created_at"] = datetime.utcnow().isoformat()
                        
                        # Create target date based on timeline
                        if goal.get("timeline_months"):
                            target_date = datetime.utcnow() + timedelta(days=goal["timeline_months"] * 30)
                            goal["target_date"] = target_date.isoformat()
                    
                    return {
                        "success": True,
                        "data": goals_data,
                        "recommendations": self._generate_goal_recommendations(goals_data),
                        "metadata": {
                            "roadmap_id": roadmap_id,
                            "total_goals": len(goals_data.get("goals", [])),
                            "generation_method": "watsonx_ai"
                        }
                    }
                    
                except json.JSONDecodeError:
                    # Fallback to basic goal creation
                    return await self._basic_goal_creation(goal_categories, timeline_months, user_profile)
            else:
                # Fallback to basic goal creation
                return await self._basic_goal_creation(goal_categories, timeline_months, user_profile)
                
        except Exception as e:
            logger.error(f"Error creating career goals: {str(e)}")
            raise
    
    async def _track_progress(self, user_profile, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Track progress on career goals and milestones
        """
        try:
            roadmap_id = task_data.get("roadmap_id")
            goal_id = task_data.get("goal_id")
            milestone_id = task_data.get("milestone_id")
            progress_data = task_data.get("progress_data", {})
            
            # Analyze progress using WatsonX.ai
            progress_prompt = f"""
            Analyze career progress and provide insights and recommendations.
            
            Progress Data:
            - Roadmap ID: {roadmap_id}
            - Goal ID: {goal_id}
            - Milestone ID: {milestone_id}
            - Progress Percentage: {progress_data.get('progress_percentage', 0)}
            - Achievements: {progress_data.get('achievements', [])}
            - Challenges: {progress_data.get('challenges', [])}
            - Time Period: {progress_data.get('period_start')} to {progress_data.get('period_end')}
            
            User Profile:
            - Current Role: {user_profile.current_role}
            - Years Experience: {user_profile.years_experience}
            
            Provide analysis on:
            1. Progress assessment and trajectory
            2. Identification of blockers and challenges
            3. Recommendations for acceleration
            4. Adjustments to timeline or approach
            5. Next steps and priorities
            
            Return in JSON format:
            {{
                "progress_analysis": {{
                    "overall_assessment": "on_track|ahead|behind|at_risk",
                    "progress_velocity": "fast|normal|slow",
                    "completion_probability": 85,
                    "estimated_completion_date": "2024-06-15",
                    "key_achievements": ["achievement1", "achievement2"],
                    "main_challenges": ["challenge1", "challenge2"]
                }},
                "recommendations": [
                    {{
                        "type": "acceleration",
                        "title": "Focus on high-impact activities",
                        "description": "Prioritize activities that provide maximum learning value",
                        "priority": "high",
                        "estimated_impact": "20% faster completion"
                    }}
                ],
                "next_steps": [
                    {{
                        "action": "Complete Kubernetes basics course",
                        "timeline": "Next 2 weeks",
                        "priority": "high",
                        "resources_needed": ["Course subscription", "4 hours per week"]
                    }}
                ],
                "adjustments": {{
                    "timeline_changes": false,
                    "scope_changes": false,
                    "resource_changes": true,
                    "suggested_modifications": ["Add practice environment", "Find study partner"]
                }},
                "metrics": {{
                    "weekly_progress_rate": 5.2,
                    "milestone_completion_rate": 80,
                    "goal_alignment_score": 92,
                    "effort_efficiency": 85
                }}
            }}
            """
            
            result = await self.watsonx_client.generate_text(progress_prompt)
            
            if result["success"]:
                try:
                    progress_analysis = json.loads(result["generated_text"])
                    
                    # Create progress tracking record
                    tracking_id = str(uuid.uuid4())
                    progress_record = {
                        "tracking_id": tracking_id,
                        "user_id": user_profile.user_id,
                        "roadmap_id": roadmap_id,
                        "goal_id": goal_id,
                        "milestone_id": milestone_id,
                        "progress_percentage": progress_data.get("progress_percentage", 0),
                        "notes": progress_data.get("notes", ""),
                        "achievements": progress_data.get("achievements", []),
                        "challenges": progress_data.get("challenges", []),
                        "next_steps": progress_analysis.get("next_steps", []),
                        "recorded_at": datetime.utcnow().isoformat(),
                        "period_start": progress_data.get("period_start"),
                        "period_end": progress_data.get("period_end")
                    }
                    
                    return {
                        "success": True,
                        "data": {
                            "progress_record": progress_record,
                            "analysis": progress_analysis
                        },
                        "recommendations": progress_analysis.get("recommendations", []),
                        "metadata": {
                            "tracking_id": tracking_id,
                            "analysis_method": "watsonx_ai",
                            "assessment": progress_analysis.get("progress_analysis", {}).get("overall_assessment", "unknown")
                        }
                    }
                    
                except json.JSONDecodeError:
                    # Fallback to basic progress tracking
                    return await self._basic_progress_tracking(progress_data, user_profile)
            else:
                # Fallback to basic progress tracking
                return await self._basic_progress_tracking(progress_data, user_profile)
                
        except Exception as e:
            logger.error(f"Error tracking progress: {str(e)}")
            raise
    
    async def _analyze_market_trends(self, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Analyze market trends and update career recommendations accordingly
        """
        try:
            industry = task_data.get("industry", "Technology")
            target_role = task_data.get("target_role", "")
            location = task_data.get("location", "Global")
            
            # Analyze market trends using WatsonX.ai
            trends_prompt = f"""
            Analyze current market trends and their impact on career strategy.
            
            Focus Areas:
            - Industry: {industry}
            - Target Role: {target_role}
            - Location: {location}
            
            Provide analysis on:
            1. Current market demand for roles and skills
            2. Emerging technologies and their impact
            3. Salary trends and compensation changes
            4. Remote work and location flexibility trends
            5. Skills that are becoming obsolete
            6. Future-proof career strategies
            
            Return in JSON format:
            {{
                "market_analysis": {{
                    "industry_health": "growing|stable|declining",
                    "role_demand": "high|medium|low",
                    "salary_trend": "increasing|stable|decreasing",
                    "remote_work_adoption": 85,
                    "automation_risk": "low|medium|high"
                }},
                "trending_skills": [
                    {{"skill": "AI/ML", "demand_growth": 150, "salary_impact": 25, "urgency": "high"}},
                    {{"skill": "Cloud Architecture", "demand_growth": 120, "salary_impact": 20, "urgency": "medium"}}
                ],
                "declining_skills": [
                    {{"skill": "Legacy Systems", "decline_rate": -30, "replacement_timeline": "2-3 years"}}
                ],
                "career_recommendations": [
                    {{
                        "recommendation": "Focus on AI/ML skills development",
                        "rationale": "150% growth in demand over next 2 years",
                        "priority": "high",
                        "timeline": "6-12 months"
                    }}
                ],
                "salary_insights": {{
                    "current_range": {{"min": 120000, "max": 180000, "median": 150000}},
                    "projected_range": {{"min": 135000, "max": 200000, "median": 167500}},
                    "growth_factors": ["AI skills", "Leadership experience", "Cloud certifications"]
                }},
                "location_insights": {{
                    "top_markets": ["San Francisco", "New York", "Seattle", "Austin"],
                    "remote_opportunities": 75,
                    "relocation_recommendations": ["Consider remote-first companies", "Focus on tech hubs"]
                }}
            }}
            """
            
            result = await self.watsonx_client.generate_text(trends_prompt)
            
            if result["success"]:
                try:
                    trends_data = json.loads(result["generated_text"])
                    
                    # Add metadata
                    trends_data["analysis_metadata"] = {
                        "analysis_date": datetime.utcnow().isoformat(),
                        "industry": industry,
                        "target_role": target_role,
                        "location": location,
                        "data_sources": ["market_research", "job_postings", "salary_surveys"]
                    }
                    
                    return {
                        "success": True,
                        "data": trends_data,
                        "recommendations": trends_data.get("career_recommendations", []),
                        "metadata": {
                            "analysis_method": "watsonx_ai",
                            "industry": industry,
                            "role_demand": trends_data.get("market_analysis", {}).get("role_demand", "unknown")
                        }
                    }
                    
                except json.JSONDecodeError:
                    # Fallback to basic market analysis
                    return await self._basic_market_analysis(industry, target_role, location)
            else:
                # Fallback to basic market analysis
                return await self._basic_market_analysis(industry, target_role, location)
                
        except Exception as e:
            logger.error(f"Error analyzing market trends: {str(e)}")
            raise
    
    async def _generate_career_recommendations(self, user_profile, task_data: Dict[str, Any], db) -> Dict[str, Any]:
        """
        Generate personalized career recommendations
        """
        try:
            # Generate comprehensive career recommendations
            recommendations_prompt = f"""
            Generate personalized career recommendations based on user profile and current market conditions.
            
            User Profile:
            - Current Role: {user_profile.current_role}
            - Years Experience: {user_profile.years_experience}
            - Industry: {user_profile.industry}
            - Skills: {json.dumps(user_profile.skills, indent=2)}
            - Career Goals: {json.dumps(user_profile.career_goals, indent=2)}
            
            Provide recommendations for:
            1. Next career moves and opportunities
            2. Skills to develop for career advancement
            3. Networking strategies and target connections
            4. Education and certification priorities
            5. Timeline and action plan
            
            Return in JSON format:
            {{
                "career_opportunities": [
                    {{
                        "role": "Senior Software Engineer",
                        "match_percentage": 85,
                        "growth_potential": "high",
                        "salary_range": {{"min": 140000, "max": 180000}},
                        "required_skills": ["Leadership", "System Design"],
                        "timeline_to_readiness": "6-12 months"
                    }}
                ],
                "skill_recommendations": [
                    {{
                        "skill": "System Design",
                        "priority": "high",
                        "rationale": "Critical for senior roles",
                        "learning_path": "Online courses + practice",
                        "timeline": "3-6 months"
                    }}
                ],
                "networking_recommendations": [
                    {{
                        "strategy": "Attend tech conferences",
                        "target_personas": ["Engineering Managers", "Senior Engineers"],
                        "frequency": "Monthly",
                        "expected_connections": 10
                    }}
                ],
                "education_recommendations": [
                    {{
                        "type": "certification",
                        "name": "AWS Solutions Architect",
                        "priority": "medium",
                        "cost": 300,
                        "timeline": "2-3 months"
                    }}
                ],
                "action_plan": {{
                    "immediate_actions": ["Update LinkedIn profile", "Start system design course"],
                    "short_term": ["Complete AWS certification", "Attend 2 networking events"],
                    "long_term": ["Apply for senior roles", "Build leadership experience"]
                }}
            }}
            """
            
            result = await self.watsonx_client.generate_text(recommendations_prompt)
            
            if result["success"]:
                try:
                    recommendations_data = json.loads(result["generated_text"])
                    
                    # Format as recommendation list
                    formatted_recommendations = []
                    
                    # Add career opportunities as recommendations
                    for opportunity in recommendations_data.get("career_opportunities", []):
                        formatted_recommendations.append({
                            "type": "career_opportunity",
                            "title": f"Consider {opportunity['role']} role",
                            "description": f"Match: {opportunity['match_percentage']}%, Growth: {opportunity['growth_potential']}",
                            "priority": "high" if opportunity.get("match_percentage", 0) > 80 else "medium",
                            "action_items": [f"Develop {skill}" for skill in opportunity.get("required_skills", [])],
                            "timeline": opportunity.get("timeline_to_readiness", "6-12 months")
                        })
                    
                    # Add skill recommendations
                    for skill_rec in recommendations_data.get("skill_recommendations", []):
                        formatted_recommendations.append({
                            "type": "skill_development",
                            "title": f"Develop {skill_rec['skill']} skills",
                            "description": skill_rec.get("rationale", ""),
                            "priority": skill_rec.get("priority", "medium"),
                            "action_items": [skill_rec.get("learning_path", "")],
                            "timeline": skill_rec.get("timeline", "3-6 months")
                        })
                    
                    return {
                        "success": True,
                        "data": recommendations_data,
                        "recommendations": formatted_recommendations,
                        "metadata": {
                            "user_id": user_profile.user_id,
                            "generation_method": "watsonx_ai",
                            "total_recommendations": len(formatted_recommendations)
                        }
                    }
                    
                except json.JSONDecodeError:
                    # Fallback to basic recommendations
                    return await self._basic_career_recommendations(user_profile)
            else:
                # Fallback to basic recommendations
                return await self._basic_career_recommendations(user_profile)
                
        except Exception as e:
            logger.error(f"Error generating career recommendations: {str(e)}")
            raise
    
    # Helper methods for generating recommendations and fallbacks
    
    def _generate_roadmap_recommendations(self, roadmap_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on roadmap data"""
        recommendations = []
        
        # Add milestone-based recommendations
        for milestone in roadmap_data.get("milestones", []):
            recommendations.append({
                "type": "milestone",
                "title": f"Focus on: {milestone['title']}",
                "description": milestone.get("description", ""),
                "priority": milestone.get("priority", "medium"),
                "timeline": milestone.get("timeline", ""),
                "action_items": milestone.get("requirements", [])
            })
        
        # Add skill development recommendations
        skill_plan = roadmap_data.get("skill_development_plan", {})
        for skill in skill_plan.get("technical_skills", []):
            recommendations.append({
                "type": "skill_development",
                "title": f"Develop {skill['skill']} skills",
                "description": f"Progress from {skill['current_level']} to {skill['target_level']}",
                "priority": "high",
                "timeline": skill.get("timeline", ""),
                "action_items": ["Find learning resources", "Practice regularly", "Build projects"]
            })
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _generate_goal_recommendations(self, goals_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on goals data"""
        recommendations = []
        
        for goal in goals_data.get("goals", []):
            recommendations.append({
                "type": "goal_achievement",
                "title": f"Work towards: {goal['title']}",
                "description": goal.get("description", ""),
                "priority": "high" if goal.get("priority", 3) == 1 else "medium",
                "timeline": f"{goal.get('timeline_months', 6)} months",
                "action_items": goal.get("success_criteria", [])
            })
        
        return recommendations
    
    # Fallback methods for when AI generation fails
    
    async def _basic_roadmap_generation(self, current_role: str, target_role: str, 
                                      timeline_months: int, user_profile) -> Dict[str, Any]:
        """Basic roadmap generation fallback"""
        roadmap_id = str(uuid.uuid4())
        
        basic_roadmap = {
            "roadmap": {
                "roadmap_id": roadmap_id,
                "title": f"Career Transition: {current_role} to {target_role}",
                "description": f"Basic roadmap for transitioning to {target_role}",
                "transition_type": "vertical",
                "timeline_months": timeline_months,
                "created_at": datetime.utcnow().isoformat()
            },
            "milestones": [
                {
                    "milestone_id": str(uuid.uuid4()),
                    "title": "Skill Assessment and Gap Analysis",
                    "type": "assessment",
                    "timeline": "Month 1",
                    "priority": "high"
                },
                {
                    "milestone_id": str(uuid.uuid4()),
                    "title": "Complete Relevant Certification",
                    "type": "certification",
                    "timeline": f"Month {timeline_months // 2}",
                    "priority": "high"
                }
            ],
            "goals": [
                {
                    "goal_id": str(uuid.uuid4()),
                    "title": "Develop Technical Skills",
                    "category": "skill_development",
                    "priority": 1,
                    "timeline_months": timeline_months // 2
                }
            ]
        }
        
        return {
            "success": True,
            "data": basic_roadmap,
            "recommendations": [],
            "metadata": {"generation_method": "basic_fallback"}
        }
    
    async def _basic_goal_creation(self, categories: List[str], timeline_months: int, 
                                 user_profile) -> Dict[str, Any]:
        """Basic goal creation fallback"""
        goals = []
        
        for i, category in enumerate(categories):
            goals.append({
                "goal_id": str(uuid.uuid4()),
                "title": f"Improve {category.replace('_', ' ').title()}",
                "category": category,
                "priority": i + 1,
                "timeline_months": timeline_months,
                "success_criteria": [f"Complete {category} objectives"],
                "created_at": datetime.utcnow().isoformat()
            })
        
        return {
            "success": True,
            "data": {"goals": goals},
            "recommendations": [],
            "metadata": {"generation_method": "basic_fallback"}
        }
    
    async def _basic_progress_tracking(self, progress_data: Dict[str, Any], 
                                     user_profile) -> Dict[str, Any]:
        """Basic progress tracking fallback"""
        tracking_id = str(uuid.uuid4())
        
        progress_record = {
            "tracking_id": tracking_id,
            "user_id": user_profile.user_id,
            "progress_percentage": progress_data.get("progress_percentage", 0),
            "recorded_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "data": {"progress_record": progress_record},
            "recommendations": [],
            "metadata": {"generation_method": "basic_fallback"}
        }
    
    async def _basic_market_analysis(self, industry: str, target_role: str, 
                                   location: str) -> Dict[str, Any]:
        """Basic market analysis fallback"""
        basic_analysis = {
            "market_analysis": {
                "industry_health": "stable",
                "role_demand": "medium",
                "salary_trend": "stable"
            },
            "trending_skills": [
                {"skill": "Cloud Computing", "demand_growth": 100},
                {"skill": "Data Analysis", "demand_growth": 80}
            ],
            "career_recommendations": [
                {
                    "recommendation": "Focus on cloud skills",
                    "priority": "high",
                    "timeline": "6 months"
                }
            ]
        }
        
        return {
            "success": True,
            "data": basic_analysis,
            "recommendations": basic_analysis["career_recommendations"],
            "metadata": {"generation_method": "basic_fallback"}
        }
    
    async def _basic_career_recommendations(self, user_profile) -> Dict[str, Any]:
        """Basic career recommendations fallback"""
        recommendations = [
            {
                "type": "skill_development",
                "title": "Continue learning new technologies",
                "description": "Stay current with industry trends",
                "priority": "medium",
                "timeline": "Ongoing"
            },
            {
                "type": "networking",
                "title": "Expand professional network",
                "description": "Connect with industry professionals",
                "priority": "medium",
                "timeline": "Ongoing"
            }
        ]
        
        return {
            "success": True,
            "data": {"recommendations": recommendations},
            "recommendations": recommendations,
            "metadata": {"generation_method": "basic_fallback"}
        }    
  
  # Abstract method implementations required by BaseAgent
    
    async def _process_request_impl(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementation of request processing for career strategy
        """
        try:
            task_type = user_input.get("task_type", "generate_roadmap")
            user_id = user_input.get("user_id") or context.get("user_id")
            
            if task_type == "generate_roadmap":
                current_role = user_input.get("current_role", "")
                target_role = user_input.get("target_role", "")
                timeline = user_input.get("timeline", "12 months")
                
                roadmap = await self.generate_career_roadmap(
                    current_role=current_role,
                    target_role=target_role,
                    timeline=timeline,
                    user_context=context
                )
                
                return {
                    "success": True,
                    "data": roadmap,
                    "recommendations": [
                        {
                            "type": "career_roadmap",
                            "description": f"Career roadmap from {current_role} to {target_role}",
                            "action": "review_roadmap",
                            "priority": "high"
                        }
                    ],
                    "metadata": {
                        "current_role": current_role,
                        "target_role": target_role,
                        "timeline": timeline,
                        "generation_timestamp": datetime.utcnow().isoformat()
                    }
                }
            
            elif task_type == "analyze_market_trends":
                industry = user_input.get("industry", "")
                role = user_input.get("role", "")
                
                trends = await self.analyze_market_trends(industry=industry, role=role)
                
                return {
                    "success": True,
                    "data": trends,
                    "recommendations": [
                        {
                            "type": "market_insights",
                            "description": "Review market trends for strategic planning",
                            "action": "analyze_trends",
                            "priority": "medium"
                        }
                    ],
                    "metadata": {
                        "industry": industry,
                        "role": role,
                        "analysis_timestamp": datetime.utcnow().isoformat()
                    }
                }
            
            elif task_type == "track_progress":
                goals = user_input.get("goals", [])
                
                progress = await self.track_career_progress(goals)
                
                return {
                    "success": True,
                    "data": progress,
                    "recommendations": [
                        {
                            "type": "progress_review",
                            "description": "Review your career progress and adjust goals",
                            "action": "update_goals",
                            "priority": "medium"
                        }
                    ],
                    "metadata": {
                        "goals_count": len(goals),
                        "tracking_timestamp": datetime.utcnow().isoformat()
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
        Implementation of recommendations generation for career strategy
        """
        try:
            recommendations = []
            
            # Generate career strategy recommendations
            current_role = user_profile.get("current_role", "")
            target_role = user_profile.get("target_role", "")
            career_goals = user_profile.get("career_goals", [])
            years_experience = user_profile.get("years_experience", 0)
            
            if current_role and target_role and current_role != target_role:
                recommendations.append({
                    "type": "career_transition",
                    "description": f"Create a roadmap from {current_role} to {target_role}",
                    "action": "generate_roadmap",
                    "priority": "high",
                    "metadata": {
                        "current_role": current_role,
                        "target_role": target_role
                    }
                })
            
            if years_experience >= 5:
                recommendations.append({
                    "type": "leadership_development",
                    "description": "Consider developing leadership skills for career advancement",
                    "action": "explore_leadership_roles",
                    "priority": "medium",
                    "metadata": {
                        "experience_level": "senior"
                    }
                })
            
            if not career_goals:
                recommendations.append({
                    "type": "goal_setting",
                    "description": "Set clear career goals to guide your professional development",
                    "action": "define_career_goals",
                    "priority": "high",
                    "metadata": {
                        "suggested_timeline": "6-12 months"
                    }
                })
            
            recommendations.append({
                "type": "market_analysis",
                "description": "Stay updated on industry trends and market demands",
                "action": "analyze_market_trends",
                "priority": "low",
                "metadata": {
                    "frequency": "quarterly"
                }
            })
            
            return recommendations
                
        except Exception as e:
            logger.error(f"Error in _get_recommendations_impl: {str(e)}")
            return []