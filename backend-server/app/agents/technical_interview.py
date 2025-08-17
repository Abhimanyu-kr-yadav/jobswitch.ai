"""
Technical Interview Agent
Handles coding challenges, DSA practice, and technical interview simulation
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4
import random

from app.agents.base import BaseAgent
from app.models.coding_challenge import (
    TechnicalInterviewSession, CodingChallenge, CodeSubmission, TechnicalInterviewFeedback,
    CodingDifficulty, CodingCategory, ProgrammingLanguage, ExecutionResult
)
from app.data.coding_challenges import (
    get_coding_challenges, get_challenges_by_category, get_challenges_by_difficulty,
    get_challenge_by_id, get_challenges_for_company
)
from app.services.code_executor import CodeExecutor

logger = logging.getLogger(__name__)


class TechnicalInterviewAgent(BaseAgent):
    """AI agent for technical interviews and coding challenges"""
    
    def __init__(self, watsonx_client=None, langchain_manager=None):
        super().__init__("technical_interview", watsonx_client, langchain_manager)
        self.watsonx_client = watsonx_client
        self.langchain_manager = langchain_manager
        self.active_sessions = {}
        self.code_executor = CodeExecutor(watsonx_client)
        self.challenges_cache = None
    
    async def process_request(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process technical interview requests"""
        try:
            action = user_input.get("action")
            
            if action == "get_challenges":
                return await self._get_challenges(user_input, context)
            elif action == "start_technical_interview":
                return await self._start_technical_interview(user_input, context)
            elif action == "get_current_challenge":
                return await self._get_current_challenge(user_input, context)
            elif action == "submit_code":
                return await self._submit_code(user_input, context)
            elif action == "execute_code":
                return await self._execute_code(user_input, context)
            elif action == "get_hint":
                return await self._get_hint(user_input, context)
            elif action == "skip_challenge":
                return await self._skip_challenge(user_input, context)
            elif action == "end_technical_interview":
                return await self._end_technical_interview(user_input, context)
            elif action == "get_technical_feedback":
                return await self._get_technical_feedback(user_input, context)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Technical interview agent error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_recommendations(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate technical interview recommendations"""
        try:
            recommendations = []
            
            # Get user's target roles and skills
            target_roles = user_profile.get("career_goals", {}).get("target_roles", [])
            skills = user_profile.get("skills", [])
            
            # Recommend practice based on role
            for role in target_roles:
                if any(keyword in role.lower() for keyword in ["engineer", "developer", "programmer"]):
                    recommendations.append({
                        "type": "technical_practice",
                        "title": f"Technical Interview Practice for {role}",
                        "description": f"Practice coding challenges commonly asked for {role} positions",
                        "priority": "high",
                        "estimated_time": "45-60 minutes",
                        "action": {
                            "type": "start_technical_interview",
                            "role": role,
                            "difficulty": "medium"
                        }
                    })
            
            # Recommend specific categories based on skills
            skill_names = [skill.get("name", "").lower() for skill in skills]
            if any(skill in skill_names for skill in ["algorithm", "data structure"]):
                recommendations.append({
                    "type": "dsa_practice",
                    "title": "Data Structures & Algorithms Practice",
                    "description": "Strengthen your DSA skills with targeted practice problems",
                    "priority": "medium",
                    "estimated_time": "30-45 minutes",
                    "action": {
                        "type": "start_technical_interview",
                        "categories": ["arrays", "trees", "dynamic_programming"]
                    }
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate technical interview recommendations: {str(e)}")
            return []
    
    async def _get_challenges(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get coding challenges with optional filtering"""
        try:
            # Get filter parameters
            difficulty = user_input.get("difficulty")
            category = user_input.get("category")
            company = user_input.get("company")
            limit = user_input.get("limit", 20)
            offset = user_input.get("offset", 0)
            
            # Load challenges if not cached
            if not self.challenges_cache:
                self.challenges_cache = get_coding_challenges()
            
            challenges = self.challenges_cache.copy()
            
            # Apply filters
            if difficulty:
                challenges = [c for c in challenges if c.difficulty == difficulty]
            
            if category:
                challenges = [c for c in challenges if c.category == category]
            
            if company:
                challenges = [c for c in challenges if company.lower() in [comp.lower() for comp in c.companies]]
            
            # Apply pagination
            total_count = len(challenges)
            challenges = challenges[offset:offset + limit]
            
            # Convert to dict format (excluding solutions for security)
            challenge_data = []
            for challenge in challenges:
                challenge_dict = challenge.dict()
                # Remove solutions from public API
                challenge_dict.pop("solution", None)
                challenge_data.append(challenge_dict)
            
            return {
                "success": True,
                "data": {
                    "challenges": challenge_data,
                    "total_count": total_count,
                    "offset": offset,
                    "limit": limit
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get challenges: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _start_technical_interview(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new technical interview session"""
        try:
            user_id = context.get("user_id", "test_user")
            session_id = str(uuid4())
            
            job_role = user_input.get("job_role", "Software Engineer")
            company = user_input.get("company", "")
            difficulty = user_input.get("difficulty", CodingDifficulty.MEDIUM)
            categories = user_input.get("categories", [])
            challenge_count = user_input.get("challenge_count", 3)
            time_limit = user_input.get("time_limit", 3600)  # 1 hour default
            
            # Select challenges based on criteria
            selected_challenges = await self._select_challenges(
                difficulty, categories, company, challenge_count
            )
            
            if not selected_challenges:
                return {"success": False, "error": "No suitable challenges found"}
            
            # Create session
            session = TechnicalInterviewSession(
                session_id=session_id,
                user_id=user_id,
                job_role=job_role,
                company=company,
                challenges=[c.id for c in selected_challenges],
                current_challenge_index=0,
                submissions=[],
                status="active",
                started_at=datetime.utcnow(),
                total_score=0
            )
            
            # Store session
            self.active_sessions[session_id] = {
                "session": session,
                "challenges": selected_challenges
            }
            
            # Return first challenge
            first_challenge = selected_challenges[0]
            challenge_data = first_challenge.dict()
            challenge_data.pop("solution", None)  # Remove solution
            
            return {
                "success": True,
                "data": {
                    "session_id": session_id,
                    "total_challenges": len(selected_challenges),
                    "current_challenge": challenge_data,
                    "session_status": session.status,
                    "time_limit": time_limit,
                    "progress": {
                        "current": 1,
                        "total": len(selected_challenges)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to start technical interview: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _select_challenges(
        self, 
        difficulty: CodingDifficulty, 
        categories: List[CodingCategory], 
        company: str, 
        count: int
    ) -> List[CodingChallenge]:
        """Select appropriate challenges for the interview"""
        try:
            # Load all challenges
            all_challenges = get_coding_challenges()
            
            # Filter by criteria
            filtered_challenges = []
            
            for challenge in all_challenges:
                # Check difficulty
                if difficulty and challenge.difficulty != difficulty:
                    continue
                
                # Check categories
                if categories and challenge.category not in categories:
                    continue
                
                # Check company
                if company and company.lower() not in [comp.lower() for comp in challenge.companies]:
                    continue
                
                filtered_challenges.append(challenge)
            
            # If no specific filters, use all challenges
            if not filtered_challenges:
                filtered_challenges = all_challenges
            
            # Select random challenges
            if len(filtered_challenges) <= count:
                return filtered_challenges
            else:
                return random.sample(filtered_challenges, count)
                
        except Exception as e:
            logger.error(f"Failed to select challenges: {str(e)}")
            return []
    
    async def _get_current_challenge(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get the current challenge for an active session"""
        try:
            session_id = user_input.get("session_id")
            
            if not session_id or session_id not in self.active_sessions:
                return {"success": False, "error": "Invalid or expired session"}
            
            session_data = self.active_sessions[session_id]
            session = session_data["session"]
            challenges = session_data["challenges"]
            
            if session.current_challenge_index >= len(challenges):
                return {"success": False, "error": "No more challenges in session"}
            
            current_challenge = challenges[session.current_challenge_index]
            challenge_data = current_challenge.dict()
            challenge_data.pop("solution", None)  # Remove solution
            
            return {
                "success": True,
                "data": {
                    "challenge": challenge_data,
                    "progress": {
                        "current": session.current_challenge_index + 1,
                        "total": len(challenges)
                    },
                    "session_status": session.status
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get current challenge: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _submit_code(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Submit code solution for evaluation"""
        try:
            session_id = user_input.get("session_id")
            challenge_id = user_input.get("challenge_id")
            language = user_input.get("language")
            code = user_input.get("code")
            
            if not all([session_id, challenge_id, language, code]):
                return {"success": False, "error": "Missing required parameters"}
            
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Invalid or expired session"}
            
            session_data = self.active_sessions[session_id]
            session = session_data["session"]
            challenges = session_data["challenges"]
            
            # Find the challenge
            challenge = None
            for c in challenges:
                if c.id == challenge_id:
                    challenge = c
                    break
            
            if not challenge:
                return {"success": False, "error": "Challenge not found"}
            
            # Create submission
            submission_id = str(uuid4())
            submission = CodeSubmission(
                submission_id=submission_id,
                challenge_id=challenge_id,
                user_id=session.user_id,
                language=ProgrammingLanguage(language),
                code=code,
                submitted_at=datetime.utcnow(),
                status="submitted"
            )
            
            # Execute code
            execution_result = await self.code_executor.execute_code(
                code, ProgrammingLanguage(language), challenge.test_cases, submission_id
            )
            
            # Update submission with results
            submission.status = execution_result.overall_status
            submission.execution_time = execution_result.execution_time
            submission.memory_used = execution_result.memory_used
            
            # Store submission
            session.submissions.append(submission)
            
            # Calculate score for this challenge
            challenge_score = self._calculate_challenge_score(execution_result, challenge)
            
            # Check if all test cases passed
            if execution_result.overall_status == "accepted":
                # Move to next challenge
                session.current_challenge_index += 1
                session.total_score += challenge_score
                
                # Check if interview is complete
                if session.current_challenge_index >= len(challenges):
                    session.status = "completed"
                    session.completed_at = datetime.utcnow()
                    
                    return {
                        "success": True,
                        "data": {
                            "execution_result": execution_result.dict(),
                            "challenge_score": challenge_score,
                            "interview_complete": True,
                            "total_score": session.total_score,
                            "session_id": session_id
                        }
                    }
                else:
                    # Return next challenge
                    next_challenge = challenges[session.current_challenge_index]
                    next_challenge_data = next_challenge.dict()
                    next_challenge_data.pop("solution", None)
                    
                    return {
                        "success": True,
                        "data": {
                            "execution_result": execution_result.dict(),
                            "challenge_score": challenge_score,
                            "interview_complete": False,
                            "next_challenge": next_challenge_data,
                            "progress": {
                                "current": session.current_challenge_index + 1,
                                "total": len(challenges)
                            }
                        }
                    }
            else:
                # Return execution results for failed submission
                return {
                    "success": True,
                    "data": {
                        "execution_result": execution_result.dict(),
                        "challenge_score": challenge_score,
                        "interview_complete": False,
                        "can_retry": True
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to submit code: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _execute_code(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code without submitting (for testing)"""
        try:
            challenge_id = user_input.get("challenge_id")
            language = user_input.get("language")
            code = user_input.get("code")
            custom_test_cases = user_input.get("test_cases")
            
            if not all([challenge_id, language, code]):
                return {"success": False, "error": "Missing required parameters"}
            
            # Get challenge
            challenge = get_challenge_by_id(challenge_id)
            if not challenge:
                return {"success": False, "error": "Challenge not found"}
            
            # Use custom test cases if provided, otherwise use challenge test cases
            test_cases = custom_test_cases if custom_test_cases else challenge.test_cases
            
            # Execute code
            execution_result = await self.code_executor.execute_code(
                code, ProgrammingLanguage(language), test_cases, str(uuid4())
            )
            
            return {
                "success": True,
                "data": {
                    "execution_result": execution_result.dict()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to execute code: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_hint(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get hint for current challenge"""
        try:
            session_id = user_input.get("session_id")
            hint_level = user_input.get("hint_level", 1)
            
            if not session_id or session_id not in self.active_sessions:
                return {"success": False, "error": "Invalid or expired session"}
            
            session_data = self.active_sessions[session_id]
            session = session_data["session"]
            challenges = session_data["challenges"]
            
            if session.current_challenge_index >= len(challenges):
                return {"success": False, "error": "No active challenge"}
            
            current_challenge = challenges[session.current_challenge_index]
            
            # Get hint based on level
            hints = current_challenge.hints
            if hint_level <= len(hints):
                hint = hints[hint_level - 1]
            else:
                # Generate AI hint if available
                if self.watsonx_client:
                    hint = await self._generate_ai_hint(current_challenge, hint_level)
                else:
                    hint = "No more hints available"
            
            return {
                "success": True,
                "data": {
                    "hint": hint,
                    "hint_level": hint_level,
                    "total_hints": len(hints)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get hint: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _skip_challenge(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Skip current challenge and move to next"""
        try:
            session_id = user_input.get("session_id")
            
            if not session_id or session_id not in self.active_sessions:
                return {"success": False, "error": "Invalid or expired session"}
            
            session_data = self.active_sessions[session_id]
            session = session_data["session"]
            challenges = session_data["challenges"]
            
            # Move to next challenge
            session.current_challenge_index += 1
            
            # Check if interview is complete
            if session.current_challenge_index >= len(challenges):
                session.status = "completed"
                session.completed_at = datetime.utcnow()
                
                return {
                    "success": True,
                    "data": {
                        "challenge_skipped": True,
                        "interview_complete": True,
                        "total_score": session.total_score
                    }
                }
            else:
                # Return next challenge
                next_challenge = challenges[session.current_challenge_index]
                next_challenge_data = next_challenge.dict()
                next_challenge_data.pop("solution", None)
                
                return {
                    "success": True,
                    "data": {
                        "challenge_skipped": True,
                        "interview_complete": False,
                        "next_challenge": next_challenge_data,
                        "progress": {
                            "current": session.current_challenge_index + 1,
                            "total": len(challenges)
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to skip challenge: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _end_technical_interview(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """End technical interview session"""
        try:
            session_id = user_input.get("session_id")
            
            if not session_id or session_id not in self.active_sessions:
                return {"success": False, "error": "Invalid or expired session"}
            
            session_data = self.active_sessions[session_id]
            session = session_data["session"]
            
            session.status = "ended"
            session.completed_at = datetime.utcnow()
            
            return {
                "success": True,
                "data": {
                    "session_ended": True,
                    "session_id": session_id,
                    "total_score": session.total_score,
                    "submissions_count": len(session.submissions)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to end technical interview: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_technical_feedback(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive technical interview feedback"""
        try:
            session_id = user_input.get("session_id")
            
            if not session_id or session_id not in self.active_sessions:
                return {"success": False, "error": "Invalid or expired session"}
            
            session_data = self.active_sessions[session_id]
            session = session_data["session"]
            challenges = session_data["challenges"]
            
            if session.status not in ["completed", "ended"]:
                return {"success": False, "error": "Session must be completed to generate feedback"}
            
            # Generate comprehensive feedback
            feedback = await self._generate_comprehensive_feedback(session, challenges)
            
            return {
                "success": True,
                "data": {
                    "session_id": session_id,
                    "feedback": feedback.dict(),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate technical feedback: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _calculate_challenge_score(self, execution_result: ExecutionResult, challenge: CodingChallenge) -> int:
        """Calculate score for a challenge based on execution results"""
        if execution_result.overall_status == "accepted":
            base_score = 100
            
            # Adjust for difficulty
            if challenge.difficulty == CodingDifficulty.EASY:
                base_score = 80
            elif challenge.difficulty == CodingDifficulty.HARD:
                base_score = 120
            
            # Adjust for execution time (bonus for fast solutions)
            if execution_result.execution_time < 1000:  # Less than 1 second
                base_score += 10
            
            return base_score
        else:
            # Partial credit for partial solutions
            return int((execution_result.passed_tests / execution_result.total_tests) * 50)
    
    async def _generate_ai_hint(self, challenge: CodingChallenge, hint_level: int) -> str:
        """Generate AI-powered hint for challenge"""
        try:
            if not self.watsonx_client:
                return "AI hints not available"
            
            prompt = f"""
            Generate a helpful hint for this coding challenge (hint level {hint_level}):
            
            Problem: {challenge.title}
            Description: {challenge.description}
            Difficulty: {challenge.difficulty}
            Category: {challenge.category}
            
            Provide a hint that:
            - Doesn't give away the complete solution
            - Guides the thinking process
            - Is appropriate for hint level {hint_level} (higher levels can be more specific)
            - Helps with the algorithmic approach
            
            Keep the hint concise and educational.
            """
            
            if hasattr(self.watsonx_client, 'generate_text'):
                hint = await self.watsonx_client.generate_text(
                    prompt=prompt,
                    max_tokens=200,
                    temperature=0.5
                )
                return hint
            
        except Exception as e:
            logger.error(f"AI hint generation failed: {str(e)}")
        
        return "Unable to generate hint at this time"
    
    async def _generate_comprehensive_feedback(
        self, 
        session: TechnicalInterviewSession, 
        challenges: List[CodingChallenge]
    ) -> TechnicalInterviewFeedback:
        """Generate comprehensive feedback for technical interview"""
        try:
            # Calculate scores
            total_challenges = len(challenges)
            completed_challenges = len(session.submissions)
            successful_submissions = sum(1 for sub in session.submissions if sub.status == "accepted")
            
            overall_score = int((session.total_score / (total_challenges * 100)) * 100) if total_challenges > 0 else 0
            problem_solving_score = int((successful_submissions / total_challenges) * 100) if total_challenges > 0 else 0
            
            # Analyze code quality and efficiency
            code_quality_score = await self._analyze_code_quality(session.submissions)
            efficiency_score = await self._analyze_efficiency(session.submissions, challenges)
            
            # Generate strengths and improvements
            strengths = self._identify_strengths(session, challenges)
            improvements = self._identify_improvements(session, challenges)
            
            # Generate detailed feedback for each challenge
            detailed_feedback = []
            for i, submission in enumerate(session.submissions):
                challenge = next((c for c in challenges if c.id == submission.challenge_id), None)
                if challenge:
                    feedback_item = {
                        "challenge_title": challenge.title,
                        "challenge_difficulty": challenge.difficulty,
                        "submission_status": submission.status,
                        "execution_time": submission.execution_time,
                        "memory_used": submission.memory_used,
                        "language": submission.language,
                        "feedback": f"Solution {'passed' if submission.status == 'accepted' else 'failed'} for {challenge.title}"
                    }
                    detailed_feedback.append(feedback_item)
            
            # Generate recommendations
            recommendations = self._generate_improvement_recommendations(session, challenges)
            
            feedback = TechnicalInterviewFeedback(
                session_id=session.session_id,
                overall_score=overall_score,
                problem_solving_score=problem_solving_score,
                code_quality_score=code_quality_score,
                efficiency_score=efficiency_score,
                communication_score=75,  # Default since we don't track communication in coding
                strengths=strengths,
                areas_for_improvement=improvements,
                detailed_feedback=detailed_feedback,
                recommendations=recommendations,
                generated_at=datetime.utcnow()
            )
            
            return feedback
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive feedback: {str(e)}")
            # Return basic feedback as fallback
            return TechnicalInterviewFeedback(
                session_id=session.session_id,
                overall_score=50,
                problem_solving_score=50,
                code_quality_score=50,
                efficiency_score=50,
                communication_score=50,
                strengths=["Completed technical interview"],
                areas_for_improvement=["Continue practicing coding challenges"],
                detailed_feedback=[],
                recommendations=["Practice more coding problems"],
                generated_at=datetime.utcnow()
            )
    
    async def _analyze_code_quality(self, submissions: List[CodeSubmission]) -> int:
        """Analyze code quality from submissions"""
        if not submissions:
            return 50
        
        # Simple heuristics for code quality
        quality_score = 70  # Base score
        
        for submission in submissions:
            code_lines = submission.code.split('\n')
            
            # Check for comments
            comment_lines = sum(1 for line in code_lines if line.strip().startswith('#') or line.strip().startswith('//'))
            if comment_lines > 0:
                quality_score += 5
            
            # Check for meaningful variable names (simple heuristic)
            if len([line for line in code_lines if 'temp' in line or 'x' in line]) < len(code_lines) * 0.3:
                quality_score += 5
            
            # Penalize very long functions
            if len(code_lines) > 50:
                quality_score -= 10
        
        return min(100, max(0, quality_score))
    
    async def _analyze_efficiency(self, submissions: List[CodeSubmission], challenges: List[CodingChallenge]) -> int:
        """Analyze algorithm efficiency"""
        if not submissions:
            return 50
        
        efficiency_score = 70  # Base score
        
        for submission in submissions:
            # Reward fast execution times
            if submission.execution_time and submission.execution_time < 1000:  # Less than 1 second
                efficiency_score += 10
            elif submission.execution_time and submission.execution_time > 5000:  # More than 5 seconds
                efficiency_score -= 10
        
        return min(100, max(0, efficiency_score))
    
    def _identify_strengths(self, session: TechnicalInterviewSession, challenges: List[CodingChallenge]) -> List[str]:
        """Identify candidate strengths"""
        strengths = []
        
        successful_submissions = [sub for sub in session.submissions if sub.status == "accepted"]
        
        if len(successful_submissions) > 0:
            strengths.append("Successfully solved coding challenges")
        
        if len(successful_submissions) == len(challenges):
            strengths.append("Completed all challenges successfully")
        
        # Check for fast solutions
        fast_solutions = [sub for sub in session.submissions if sub.execution_time and sub.execution_time < 2000]
        if fast_solutions:
            strengths.append("Efficient algorithm implementation")
        
        # Check language diversity
        languages_used = set(sub.language for sub in session.submissions)
        if len(languages_used) > 1:
            strengths.append("Multi-language programming proficiency")
        
        return strengths or ["Participated in technical interview"]
    
    def _identify_improvements(self, session: TechnicalInterviewSession, challenges: List[CodingChallenge]) -> List[str]:
        """Identify areas for improvement"""
        improvements = []
        
        failed_submissions = [sub for sub in session.submissions if sub.status != "accepted"]
        
        if failed_submissions:
            improvements.append("Algorithm correctness and edge case handling")
        
        if len(session.submissions) < len(challenges):
            improvements.append("Time management and problem completion")
        
        # Check for slow solutions
        slow_solutions = [sub for sub in session.submissions if sub.execution_time and sub.execution_time > 5000]
        if slow_solutions:
            improvements.append("Algorithm efficiency and optimization")
        
        return improvements or ["Continue practicing coding challenges"]
    
    def _generate_improvement_recommendations(self, session: TechnicalInterviewSession, challenges: List[CodingChallenge]) -> List[str]:
        """Generate specific improvement recommendations"""
        recommendations = []
        
        # Analyze failed challenges
        failed_categories = set()
        for submission in session.submissions:
            if submission.status != "accepted":
                challenge = next((c for c in challenges if c.id == submission.challenge_id), None)
                if challenge:
                    failed_categories.add(challenge.category)
        
        for category in failed_categories:
            recommendations.append(f"Practice more {category.replace('_', ' ')} problems")
        
        # General recommendations
        if len(session.submissions) < len(challenges):
            recommendations.append("Work on time management during coding interviews")
        
        recommendations.append("Review data structures and algorithms fundamentals")
        recommendations.append("Practice explaining your thought process while coding")
        
        return recommendations    

    # Abstract method implementations required by BaseAgent
    
    async def _process_request_impl(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementation of request processing for technical interview
        """
        try:
            task_type = user_input.get("task_type", "generate_challenge")
            user_id = user_input.get("user_id") or context.get("user_id")
            
            if task_type == "generate_challenge":
                difficulty = user_input.get("difficulty", "medium")
                topic = user_input.get("topic", "algorithms")
                programming_language = user_input.get("programming_language", "python")
                
                challenge = await self.generate_coding_challenge(
                    difficulty=difficulty,
                    topic=topic,
                    programming_language=programming_language
                )
                
                return {
                    "success": True,
                    "data": challenge,
                    "recommendations": [
                        {
                            "type": "coding_practice",
                            "description": f"Practice {difficulty} level {topic} challenge",
                            "action": "start_challenge",
                            "priority": "high"
                        }
                    ],
                    "metadata": {
                        "difficulty": difficulty,
                        "topic": topic,
                        "language": programming_language,
                        "generation_timestamp": datetime.utcnow().isoformat()
                    }
                }
            
            elif task_type == "evaluate_solution":
                code_solution = user_input.get("code_solution", "")
                challenge_id = user_input.get("challenge_id", "")
                
                evaluation = await self.evaluate_code_solution(
                    code_solution=code_solution,
                    challenge_id=challenge_id
                )
                
                return {
                    "success": True,
                    "data": evaluation,
                    "recommendations": [
                        {
                            "type": "code_improvement",
                            "description": "Review feedback and improve your solution",
                            "action": "refactor_code",
                            "priority": "medium"
                        }
                    ],
                    "metadata": {
                        "challenge_id": challenge_id,
                        "evaluation_timestamp": datetime.utcnow().isoformat()
                    }
                }
            
            elif task_type == "conduct_technical_interview":
                role = user_input.get("role", "Software Engineer")
                duration = user_input.get("duration", 60)
                
                interview = await self.conduct_technical_interview(
                    role=role,
                    duration=duration
                )
                
                return {
                    "success": True,
                    "data": interview,
                    "recommendations": [
                        {
                            "type": "technical_interview",
                            "description": "Complete technical interview simulation",
                            "action": "start_interview",
                            "priority": "high"
                        }
                    ],
                    "metadata": {
                        "role": role,
                        "duration": duration,
                        "interview_timestamp": datetime.utcnow().isoformat()
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
        Implementation of recommendations generation for technical interview
        """
        try:
            recommendations = []
            
            # Generate technical interview recommendations
            target_role = user_profile.get("target_role", "")
            programming_languages = user_profile.get("programming_languages", [])
            experience_level = user_profile.get("experience_level", "intermediate")
            
            if "software" in target_role.lower() or "engineer" in target_role.lower():
                recommendations.append({
                    "type": "coding_practice",
                    "description": "Practice coding challenges to prepare for technical interviews",
                    "action": "start_coding_practice",
                    "priority": "high",
                    "metadata": {
                        "target_role": target_role,
                        "experience_level": experience_level
                    }
                })
            
            if programming_languages:
                for lang in programming_languages[:2]:  # Top 2 languages
                    recommendations.append({
                        "type": "language_specific_practice",
                        "description": f"Practice {lang} coding challenges",
                        "action": "practice_language",
                        "priority": "medium",
                        "metadata": {
                            "programming_language": lang
                        }
                    })
            
            recommendations.append({
                "type": "mock_technical_interview",
                "description": "Take a full technical interview simulation",
                "action": "start_technical_interview",
                "priority": "medium",
                "metadata": {
                    "estimated_duration": "60-90 minutes"
                }
            })
            
            return recommendations
                
        except Exception as e:
            logger.error(f"Error in _get_recommendations_impl: {str(e)}")
            return []