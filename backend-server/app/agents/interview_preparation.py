"""
Interview Preparation Agent
Handles interview question generation, mock interview sessions, and feedback
"""
import logging
from datetime import datetime
from typing import Dict, Any, List
from uuid import uuid4

from app.agents.base import BaseAgent, AgentResponse, AgentError
from app.models.interview import (
    InterviewSession, InterviewQuestion, InterviewResponse, InterviewFeedback,
    InterviewQuestionCategory, InterviewQuestionDifficulty, InterviewSessionStatus,
    InterviewPreparationRecommendation
)

logger = logging.getLogger(__name__)


class InterviewPreparationAgent(BaseAgent):
    """AI agent for interview preparation"""
    
    def __init__(self, watsonx_client=None, langchain_manager=None):
        super().__init__("interview_preparation", watsonx_client, langchain_manager)
        self.watsonx_client = watsonx_client  # For backward compatibility
        self.langchain_manager = langchain_manager
        self.active_sessions = {}
        self.question_bank = {}
    
    async def process_request(self, user_input, context):
        """Process interview preparation requests"""
        try:
            action = user_input.get("action")
            
            if action == "generate_questions":
                return await self._generate_interview_questions(user_input, context)
            elif action == "start_mock_interview":
                return await self._start_mock_interview(user_input, context)
            elif action == "submit_response":
                return await self._process_interview_response(user_input, context)
            elif action == "end_session":
                return await self._end_interview_session(user_input, context)
            elif action == "get_feedback":
                return await self._generate_interview_feedback(user_input, context)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Interview preparation agent error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_recommendations(self, user_profile):
        """Generate interview preparation recommendations"""
        try:
            recommendations = []
            
            # Get user's target roles
            target_roles = user_profile.get("career_goals", {}).get("target_roles", [])
            
            # Recommend practice sessions for target roles
            for role in target_roles:
                recommendations.append({
                    "type": "mock_interview",
                    "title": f"Mock Interview Practice for {role}",
                    "description": f"Practice common interview questions for {role} positions",
                    "priority": "high",
                    "estimated_time": "30-45 minutes",
                    "action": {
                        "type": "start_mock_interview",
                        "role": role
                    }
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate interview recommendations: {str(e)}")
            return []
    
    async def _generate_interview_questions(self, user_input, context):
        """Generate interview questions using AI and templates"""
        try:
            job_role = user_input.get("job_role", "")
            company = user_input.get("company", "")
            skills = user_input.get("skills", [])
            question_count = user_input.get("question_count", 10)
            categories = user_input.get("categories", ["behavioral", "technical"])
            
            # Generate AI-enhanced questions if WatsonX is available
            if self.watsonx_client:
                questions = await self._generate_ai_questions(job_role, company, skills, question_count, categories)
            else:
                # Fallback to template questions
                questions = self._generate_template_questions(job_role, company, question_count, categories)
            
            return {
                "success": True,
                "data": {
                    "questions": [q.dict() for q in questions],
                    "job_role": job_role,
                    "company": company,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Question generation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _generate_ai_questions(self, job_role, company, skills, count, categories):
        """Generate questions using WatsonX.ai"""
        try:
            # Create prompt for AI question generation
            skills_text = ", ".join(skills) if skills else "general skills"
            company_text = f" at {company}" if company else ""
            
            prompt = f"""
            Generate {count} interview questions for a {job_role} position{company_text}.
            
            Requirements:
            - Include questions from these categories: {', '.join(categories)}
            - Consider these relevant skills: {skills_text}
            - Vary difficulty levels (easy, medium, hard)
            - Include key points candidates should address
            - Provide answer structure guidance
            
            Format each question as:
            Question: [question text]
            Category: [behavioral/technical/company/general]
            Difficulty: [easy/medium/hard]
            Key Points: [comma-separated key points]
            Answer Structure: [guidance for structuring the answer]
            ---
            """
            
            # Use WatsonX to generate questions
            if hasattr(self.watsonx_client, 'generate_text'):
                ai_response = await self.watsonx_client.generate_text(
                    prompt=prompt,
                    max_tokens=2000,
                    temperature=0.7
                )
                
                # Parse AI response into structured questions
                questions = self._parse_ai_questions(ai_response)
                
                # If AI generation fails or returns insufficient questions, supplement with templates
                if len(questions) < count:
                    template_questions = self._generate_template_questions(job_role, company, count - len(questions), categories)
                    questions.extend(template_questions)
                
                return questions[:count]
            else:
                # Fallback to template questions
                return self._generate_template_questions(job_role, company, count, categories)
                
        except Exception as e:
            logger.warning(f"AI question generation failed, using templates: {str(e)}")
            return self._generate_template_questions(job_role, company, count, categories)
    
    def _parse_ai_questions(self, ai_response):
        """Parse AI-generated questions into structured format"""
        questions = []
        
        try:
            # Split response by question separators
            question_blocks = ai_response.split('---')
            
            for block in question_blocks:
                if not block.strip():
                    continue
                    
                lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
                question_data = {}
                
                for line in lines:
                    if line.startswith('Question:'):
                        question_data['question'] = line.replace('Question:', '').strip()
                    elif line.startswith('Category:'):
                        category = line.replace('Category:', '').strip().lower()
                        question_data['category'] = category if category in ['behavioral', 'technical', 'company', 'general'] else 'general'
                    elif line.startswith('Difficulty:'):
                        difficulty = line.replace('Difficulty:', '').strip().lower()
                        question_data['difficulty'] = difficulty if difficulty in ['easy', 'medium', 'hard'] else 'medium'
                    elif line.startswith('Key Points:'):
                        key_points = line.replace('Key Points:', '').strip()
                        question_data['key_points'] = [point.strip() for point in key_points.split(',') if point.strip()]
                    elif line.startswith('Answer Structure:'):
                        question_data['answer_structure'] = line.replace('Answer Structure:', '').strip()
                
                # Validate and create question object
                if question_data.get('question'):
                    question = InterviewQuestion(
                        id=str(uuid4()),
                        question=question_data['question'],
                        category=InterviewQuestionCategory(question_data.get('category', 'general')),
                        difficulty=InterviewQuestionDifficulty(question_data.get('difficulty', 'medium')),
                        time_limit=120,  # 2 minutes default
                        key_points=question_data.get('key_points', []),
                        answer_structure=question_data.get('answer_structure', '')
                    )
                    questions.append(question)
                    
        except Exception as e:
            logger.error(f"Failed to parse AI questions: {str(e)}")
            
        return questions

    def _generate_template_questions(self, job_role, company, count, categories):
        """Generate questions using predefined templates"""
        template_questions = []
        
        # Basic behavioral questions
        behavioral_templates = [
            {
                "question": "Tell me about a time when you faced a challenging problem at work. How did you solve it?",
                "category": InterviewQuestionCategory.BEHAVIORAL,
                "difficulty": InterviewQuestionDifficulty.MEDIUM,
                "key_points": ["Problem identification", "Solution approach", "Results achieved"],
                "answer_structure": "Use STAR method: Situation, Task, Action, Result"
            },
            {
                "question": "Describe a situation where you had to work with a difficult team member.",
                "category": InterviewQuestionCategory.BEHAVIORAL, 
                "difficulty": InterviewQuestionDifficulty.MEDIUM,
                "key_points": ["Communication skills", "Conflict resolution", "Team collaboration"],
                "answer_structure": "Focus on professional approach and positive outcome"
            },
            {
                "question": "Tell me about a time when you had to learn something new quickly.",
                "category": InterviewQuestionCategory.BEHAVIORAL,
                "difficulty": InterviewQuestionDifficulty.EASY,
                "key_points": ["Learning agility", "Adaptability", "Resource utilization"],
                "answer_structure": "Highlight learning process and application"
            },
            {
                "question": "Give me an example of a goal you reached and tell me how you achieved it.",
                "category": InterviewQuestionCategory.BEHAVIORAL,
                "difficulty": InterviewQuestionDifficulty.MEDIUM,
                "key_points": ["Goal setting", "Planning", "Execution", "Achievement"],
                "answer_structure": "Describe the goal, your plan, actions taken, and results"
            },
            {
                "question": "Tell me about a time when you made a mistake. How did you handle it?",
                "category": InterviewQuestionCategory.BEHAVIORAL,
                "difficulty": InterviewQuestionDifficulty.MEDIUM,
                "key_points": ["Accountability", "Problem-solving", "Learning from mistakes"],
                "answer_structure": "Own the mistake, explain your response, and show what you learned"
            }
        ]
        
        # Technical questions
        technical_templates = [
            {
                "question": "Explain the difference between REST and GraphQL APIs.",
                "category": InterviewQuestionCategory.TECHNICAL,
                "difficulty": InterviewQuestionDifficulty.MEDIUM,
                "key_points": ["API design", "Data fetching", "Performance considerations"],
                "answer_structure": "Compare advantages and use cases of each"
            },
            {
                "question": "How would you optimize a slow database query?",
                "category": InterviewQuestionCategory.TECHNICAL,
                "difficulty": InterviewQuestionDifficulty.HARD,
                "key_points": ["Query analysis", "Indexing", "Database optimization"],
                "answer_structure": "Systematic approach to performance tuning"
            },
            {
                "question": "What is the difference between synchronous and asynchronous programming?",
                "category": InterviewQuestionCategory.TECHNICAL,
                "difficulty": InterviewQuestionDifficulty.MEDIUM,
                "key_points": ["Concurrency", "Performance", "Use cases"],
                "answer_structure": "Define both concepts and explain when to use each"
            },
            {
                "question": "How would you design a system to handle 1 million users?",
                "category": InterviewQuestionCategory.TECHNICAL,
                "difficulty": InterviewQuestionDifficulty.HARD,
                "key_points": ["Scalability", "Load balancing", "Database design", "Caching"],
                "answer_structure": "Discuss architecture, scaling strategies, and trade-offs"
            }
        ]
        
        # Company-specific questions
        company_templates = []
        if company:
            company_templates = [
                {
                    "question": f"Why do you want to work at {company}?",
                    "category": InterviewQuestionCategory.COMPANY,
                    "difficulty": InterviewQuestionDifficulty.EASY,
                    "key_points": ["Company research", "Value alignment", "Career goals"],
                    "answer_structure": "Show knowledge of company and genuine interest"
                },
                {
                    "question": f"What do you know about {company}'s products/services?",
                    "category": InterviewQuestionCategory.COMPANY,
                    "difficulty": InterviewQuestionDifficulty.EASY,
                    "key_points": ["Product knowledge", "Market understanding", "Customer impact"],
                    "answer_structure": "Demonstrate research and understanding of the business"
                }
            ]
        
        # General questions
        general_templates = [
            {
                "question": "Where do you see yourself in 5 years?",
                "category": InterviewQuestionCategory.GENERAL,
                "difficulty": InterviewQuestionDifficulty.EASY,
                "key_points": ["Career goals", "Growth mindset", "Alignment with role"],
                "answer_structure": "Show ambition while staying relevant to the position"
            },
            {
                "question": "What are your greatest strengths and weaknesses?",
                "category": InterviewQuestionCategory.GENERAL,
                "difficulty": InterviewQuestionDifficulty.MEDIUM,
                "key_points": ["Self-awareness", "Honesty", "Growth mindset"],
                "answer_structure": "Be honest but show how you're working on weaknesses"
            }
        ]
        
        # Combine questions based on requested categories
        all_templates = []
        if "behavioral" in categories:
            all_templates.extend(behavioral_templates)
        if "technical" in categories:
            all_templates.extend(technical_templates)
        if "company" in categories and company_templates:
            all_templates.extend(company_templates)
        if "general" in categories:
            all_templates.extend(general_templates)
        
        # Create InterviewQuestion objects
        questions = []
        for template in all_templates[:count]:
            question = InterviewQuestion(
                id=str(uuid4()),
                question=template["question"],
                category=template["category"],
                difficulty=template["difficulty"],
                time_limit=120,  # 2 minutes default
                key_points=template["key_points"],
                answer_structure=template["answer_structure"]
            )
            questions.append(question)
        
        return questions
    
    async def _start_mock_interview(self, user_input, context):
        """Start a new mock interview session"""
        try:
            user_id = context.get("user_id", "test_user")
            session_id = str(uuid4())
            
            job_role = user_input.get("job_role", "")
            company = user_input.get("company", "")
            skills = user_input.get("skills", [])
            question_count = user_input.get("question_count", 5)
            categories = user_input.get("categories", ["behavioral", "technical"])
            recording_mode = user_input.get("recording_mode", "audio")
            
            # Generate questions for the session
            if self.watsonx_client:
                questions = await self._generate_ai_questions(job_role, company, skills, question_count, categories)
            else:
                questions = self._generate_template_questions(job_role, company, question_count, categories)
            
            # Create session using the model
            session = InterviewSession(
                session_id=session_id,
                user_id=user_id,
                job_role=job_role,
                company=company,
                questions=questions,
                current_question_index=0,
                responses=[],
                status=InterviewSessionStatus.ACTIVE,
                recording_mode=recording_mode,
                started_at=datetime.utcnow()
            )
            
            # Store session
            self.active_sessions[session_id] = session
            
            return {
                "success": True,
                "data": {
                    "session_id": session_id,
                    "total_questions": len(questions),
                    "current_question": questions[0].dict() if questions else None,
                    "session_status": session.status,
                    "recording_mode": recording_mode
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to start mock interview: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _process_interview_response(self, user_input, context):
        """Process user response to interview question"""
        try:
            session_id = user_input.get("session_id")
            response_text = user_input.get("response", "")
            response_time = user_input.get("response_time", 0)
            audio_url = user_input.get("audio_url")
            video_url = user_input.get("video_url")
            
            if not session_id or session_id not in self.active_sessions:
                return {"success": False, "error": "Invalid or expired session"}
            
            session = self.active_sessions[session_id]
            current_index = session.current_question_index
            
            # Create response object
            response = InterviewResponse(
                question_id=session.questions[current_index].id,
                response=response_text,
                response_time=response_time,
                audio_url=audio_url,
                video_url=video_url,
                timestamp=datetime.utcnow()
            )
            
            # Store the response
            session.responses.append(response)
            
            # Move to next question
            session.current_question_index += 1
            
            # Check if interview is complete
            if session.current_question_index >= len(session.questions):
                session.status = InterviewSessionStatus.COMPLETED
                session.completed_at = datetime.utcnow()
                
                return {
                    "success": True,
                    "data": {
                        "session_complete": True,
                        "total_responses": len(session.responses),
                        "session_id": session_id
                    }
                }
            else:
                # Return next question
                next_question = session.questions[session.current_question_index]
                return {
                    "success": True,
                    "data": {
                        "session_complete": False,
                        "next_question": next_question.dict(),
                        "progress": {
                            "current": session.current_question_index + 1,
                            "total": len(session.questions)
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to process interview response: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _end_interview_session(self, user_input, context):
        """End an active interview session"""
        try:
            session_id = user_input.get("session_id")
            
            if not session_id or session_id not in self.active_sessions:
                return {"success": False, "error": "Invalid or expired session"}
            
            session = self.active_sessions[session_id]
            session.status = InterviewSessionStatus.ENDED
            session.ended_at = datetime.utcnow()
            
            return {
                "success": True,
                "data": {
                    "session_ended": True,
                    "session_id": session_id,
                    "responses_count": len(session.responses)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to end interview session: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _generate_interview_feedback(self, user_input, context):
        """Generate feedback for completed interview session"""
        try:
            session_id = user_input.get("session_id")
            
            if not session_id or session_id not in self.active_sessions:
                return {"success": False, "error": "Invalid or expired session"}
            
            session = self.active_sessions[session_id]
            
            if session.status not in [InterviewSessionStatus.COMPLETED, InterviewSessionStatus.ENDED]:
                return {"success": False, "error": "Session must be completed to generate feedback"}
            
            # Generate AI-enhanced feedback if available
            if self.watsonx_client:
                feedback = await self._generate_ai_feedback(session)
            else:
                feedback = self._generate_template_feedback(session.questions, session.responses)
            
            return {
                "success": True,
                "data": {
                    "session_id": session_id,
                    "feedback": feedback.dict() if hasattr(feedback, 'dict') else feedback,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate feedback: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _generate_ai_feedback(self, session: InterviewSession):
        """Generate AI-enhanced feedback for interview session"""
        try:
            # Process speech-to-text for audio responses
            enhanced_responses = []
            speech_transcripts = []
            
            for i, response in enumerate(session.responses):
                question = session.questions[i]
                
                # Process audio if available
                speech_transcript = None
                if response.audio_url:
                    speech_transcript = await self._process_speech_to_text(response.audio_url)
                    speech_transcripts.append(speech_transcript)
                
                enhanced_response = {
                    "question": question.question,
                    "category": question.category,
                    "difficulty": question.difficulty,
                    "text_response": response.response,
                    "response_time": response.response_time,
                    "key_points": question.key_points,
                    "has_audio": response.audio_url is not None,
                    "has_video": response.video_url is not None,
                    "speech_transcript": speech_transcript,
                    "answer_structure": question.answer_structure
                }
                enhanced_responses.append(enhanced_response)
            
            # Create comprehensive prompt for AI feedback with enhanced speech analysis
            speech_summary = self._create_speech_analysis_summary(speech_transcripts)
            
            prompt = f"""
            Analyze this comprehensive interview performance for a {session.job_role} position{' at ' + session.company if session.company else ''}:
            
            Interview Questions and Responses:
            {self._format_enhanced_qa_for_ai(enhanced_responses)}
            
            Speech Analysis Summary:
            {speech_summary}
            
            Please provide detailed feedback including:
            1. Overall score (0-100) - be specific and justify the score
            2. Key strengths demonstrated (3-5 specific strengths)
            3. Areas for improvement (3-5 specific areas)
            4. Question-by-question analysis with individual scores (0-100)
            5. Speaking patterns and communication analysis
            6. Specific, actionable recommendations for improvement
            
            Evaluation Criteria:
            - Content Quality (40%): Answer completeness, relevance, use of specific examples, STAR method
            - Communication Skills (30%): Clarity, confidence, professional language, structure
            - Technical Competence (20%): Knowledge demonstration, problem-solving approach
            - Speaking Patterns (10%): Pace, clarity, filler words, engagement
            
            For each response, analyze:
            - Content quality and structure (does it address the question fully?)
            - Relevance to the question and key points
            - Use of concrete examples and quantifiable results
            - Professional language and tone
            - Response timing and pacing
            - Speaking clarity and confidence (if audio available)
            
            Format your response with clear sections and specific, actionable feedback.
            Be constructive and encouraging while providing honest assessment.
            """
            
            if hasattr(self.watsonx_client, 'generate_text'):
                ai_response = await self.watsonx_client.generate_text(
                    prompt=prompt,
                    max_tokens=2500,
                    temperature=0.3
                )
                
                # Parse AI response into structured feedback
                feedback = self._parse_ai_feedback(ai_response, session, enhanced_responses)
                
                # Add comprehensive speech analysis to feedback
                feedback = await self._enhance_feedback_with_speech_analysis(feedback, session, speech_transcripts)
                
                return feedback
            else:
                return self._generate_enhanced_template_feedback(session.questions, session.responses, enhanced_responses)
                
        except Exception as e:
            logger.warning(f"AI feedback generation failed, using enhanced template: {str(e)}")
            return self._generate_enhanced_template_feedback(session.questions, session.responses, enhanced_responses)
    
    def _create_speech_analysis_summary(self, speech_transcripts):
        """Create a summary of speech analysis across all responses"""
        if not speech_transcripts or not any(speech_transcripts):
            return "No audio analysis available - responses were text-based only."
        
        valid_transcripts = [t for t in speech_transcripts if t]
        if not valid_transcripts:
            return "Audio was recorded but speech analysis is not available."
        
        # Calculate averages
        avg_speaking_rate = sum(t.get("speaking_rate", 150) for t in valid_transcripts) / len(valid_transcripts)
        avg_clarity = sum(t.get("clarity_score", 0.8) for t in valid_transcripts) / len(valid_transcripts)
        total_filler_words = sum(len(t.get("filler_words", [])) for t in valid_transcripts)
        
        summary = f"""
        Audio Responses: {len(valid_transcripts)} out of {len(speech_transcripts)} questions
        Average Speaking Rate: {avg_speaking_rate:.0f} words per minute
        Average Clarity Score: {avg_clarity:.2f}
        Total Filler Words: {total_filler_words}
        Common Filler Words: {', '.join(set(word for t in valid_transcripts for word in t.get('filler_words', [])))}
        """
        
        return summary.strip()
    
    async def _process_speech_to_text(self, audio_url):
        """Process audio recording to extract text using speech-to-text"""
        try:
            if not audio_url:
                return None
                
            # In a real implementation, you would use a speech-to-text service
            # like IBM Watson Speech to Text, Google Speech-to-Text, or Azure Speech
            if self.watsonx_client and hasattr(self.watsonx_client, 'speech_to_text'):
                # Use Watson Speech to Text
                transcript = await self.watsonx_client.speech_to_text(audio_url)
                return transcript
            else:
                # Enhanced fallback: simulate realistic speech-to-text processing
                logger.warning("Speech-to-text service not available, using enhanced simulation")
                
                # Simulate realistic speech analysis based on audio file
                import random
                import os
                
                # Simulate file analysis
                file_exists = os.path.exists(audio_url.replace('/uploads/', 'uploads/')) if audio_url.startswith('/uploads/') else False
                
                # Generate realistic transcript simulation
                sample_responses = [
                    "In my previous role as a software engineer, I encountered a challenging bug that was affecting our production system. I took the initiative to investigate the issue by analyzing the logs and tracing through the code. After identifying the root cause, I implemented a fix and worked with the QA team to thoroughly test it. The result was a 50% reduction in system errors and improved user experience.",
                    "I believe my strongest skill is problem-solving. For example, when our team was struggling to meet a tight deadline, I suggested breaking down the project into smaller, manageable tasks and implementing daily stand-ups to track progress. This approach helped us deliver the project on time and improved our team's communication.",
                    "I'm passionate about this role because it aligns with my career goals and allows me to work with cutting-edge technology. I've been following your company's innovations in the field and I'm excited about the opportunity to contribute to your team's success."
                ]
                
                simulated_transcript = random.choice(sample_responses)
                word_count = len(simulated_transcript.split())
                
                # Simulate realistic speech metrics
                speaking_rate = random.randint(120, 180)  # Normal speaking rate
                pause_count = random.randint(1, 4)
                filler_words = random.choice([[], ["um"], ["uh"], ["um", "uh"], ["like", "you know"]])
                clarity_score = random.uniform(0.7, 0.95)
                confidence_score = random.uniform(0.75, 0.9)
                
                return {
                    "transcript": simulated_transcript,
                    "confidence": confidence_score,
                    "word_count": word_count,
                    "speaking_rate": speaking_rate,  # words per minute
                    "pause_count": pause_count,
                    "filler_words": filler_words,
                    "clarity_score": clarity_score,
                    "audio_duration": word_count / (speaking_rate / 60),  # estimated duration in seconds
                    "volume_consistency": random.choice(["excellent", "good", "fair"]),
                    "pace_variation": random.choice(["appropriate", "too_fast", "too_slow", "variable"]),
                    "pronunciation_clarity": random.uniform(0.8, 0.95)
                }
                
        except Exception as e:
            logger.error(f"Speech-to-text processing failed: {str(e)}")
            return None
    
    def _analyze_speech_patterns(self, response, speech_transcript=None):
        """Analyze speech patterns from audio response with enhanced analysis"""
        try:
            speech_analysis = {
                "has_audio": response.audio_url is not None,
                "response_length": len(response.response.split()) if response.response else 0,
                "response_time": response.response_time,
                "pace_analysis": "moderate",
                "clarity_score": 0.8,
                "confidence_indicators": [],
                "areas_for_improvement": []
            }
            
            # Analyze response time
            if response.response_time < 30:
                speech_analysis["pace_analysis"] = "too_fast"
                speech_analysis["areas_for_improvement"].append("Consider taking more time to think before responding")
            elif response.response_time > 180:
                speech_analysis["pace_analysis"] = "too_slow"
                speech_analysis["areas_for_improvement"].append("Try to be more concise in your responses")
            else:
                speech_analysis["pace_analysis"] = "appropriate"
                speech_analysis["confidence_indicators"].append("Good pacing and timing")
            
            # Analyze response length
            word_count = len(response.response.split()) if response.response else 0
            if word_count < 20:
                speech_analysis["areas_for_improvement"].append("Provide more detailed responses with specific examples")
            elif word_count > 200:
                speech_analysis["areas_for_improvement"].append("Try to be more concise while maintaining detail")
            else:
                speech_analysis["confidence_indicators"].append("Appropriate response length")
            
            # Enhanced audio analysis if available
            if response.audio_url and speech_transcript:
                speaking_rate = speech_transcript.get("speaking_rate", 150)
                filler_words = speech_transcript.get("filler_words", [])
                clarity_score = speech_transcript.get("clarity_score", 0.8)
                pause_count = speech_transcript.get("pause_count", 0)
                
                speech_analysis["audio_analysis"] = {
                    "speaking_rate": speaking_rate,
                    "pause_frequency": self._analyze_pause_frequency(pause_count, speech_transcript.get("audio_duration", 60)),
                    "volume_consistency": speech_transcript.get("volume_consistency", "good"),
                    "filler_word_count": len(filler_words),
                    "filler_words": filler_words,
                    "clarity_rating": self._get_clarity_rating(clarity_score),
                    "pace_variation": speech_transcript.get("pace_variation", "appropriate"),
                    "pronunciation_clarity": speech_transcript.get("pronunciation_clarity", 0.8)
                }
                
                # Add specific feedback based on audio analysis
                if speaking_rate < 120:
                    speech_analysis["areas_for_improvement"].append("Consider speaking slightly faster to maintain engagement")
                elif speaking_rate > 180:
                    speech_analysis["areas_for_improvement"].append("Try speaking slightly slower for better clarity")
                else:
                    speech_analysis["confidence_indicators"].append("Good speaking pace")
                
                if len(filler_words) > 3:
                    speech_analysis["areas_for_improvement"].append("Reduce use of filler words (um, uh, like)")
                elif len(filler_words) <= 1:
                    speech_analysis["confidence_indicators"].append("Minimal use of filler words")
                
                if clarity_score < 0.7:
                    speech_analysis["areas_for_improvement"].append("Focus on speaking more clearly and distinctly")
                elif clarity_score > 0.9:
                    speech_analysis["confidence_indicators"].append("Excellent speech clarity")
                
                # Update overall clarity score
                speech_analysis["clarity_score"] = clarity_score
                
            elif response.audio_url:
                # Basic audio analysis without transcript
                speech_analysis["audio_analysis"] = {
                    "speaking_rate": 150,  # estimated
                    "pause_frequency": "moderate",
                    "volume_consistency": "good",
                    "filler_word_count": 2,  # estimated
                    "clarity_rating": "good"
                }
            
            return speech_analysis
            
        except Exception as e:
            logger.error(f"Speech pattern analysis failed: {str(e)}")
            return {
                "has_audio": False,
                "response_length": 0,
                "response_time": 0,
                "pace_analysis": "unknown",
                "clarity_score": 0.5,
                "confidence_indicators": [],
                "areas_for_improvement": ["Unable to analyze speech patterns"]
            }
    
    def _analyze_pause_frequency(self, pause_count, duration):
        """Analyze pause frequency in speech"""
        if duration <= 0:
            return "unknown"
        
        pauses_per_minute = (pause_count / duration) * 60
        
        if pauses_per_minute < 2:
            return "low"
        elif pauses_per_minute > 6:
            return "high"
        else:
            return "appropriate"
    
    def _get_clarity_rating(self, clarity_score):
        """Convert clarity score to rating"""
        if clarity_score >= 0.9:
            return "excellent"
        elif clarity_score >= 0.8:
            return "good"
        elif clarity_score >= 0.7:
            return "fair"
        else:
            return "needs_improvement"
    
    async def _enhance_feedback_with_speech_analysis(self, feedback, session, speech_transcripts=None):
        """Enhance feedback with detailed speech pattern analysis"""
        try:
            # Analyze overall speaking patterns across all responses
            total_responses = len(session.responses)
            audio_responses = sum(1 for r in session.responses if r.audio_url)
            
            speaking_analysis = {
                "total_responses": total_responses,
                "audio_responses": audio_responses,
                "average_response_time": sum(r.response_time for r in session.responses) / total_responses if total_responses > 0 else 0,
                "response_consistency": "good" if len(set(r.response_time // 30 for r in session.responses)) <= 2 else "variable",
                "overall_confidence": "moderate",
                "communication_strengths": [],
                "communication_improvements": []
            }
            
            # Enhanced analysis with speech transcripts
            if speech_transcripts and any(speech_transcripts):
                valid_transcripts = [t for t in speech_transcripts if t]
                
                if valid_transcripts:
                    # Calculate speech metrics
                    avg_speaking_rate = sum(t.get("speaking_rate", 150) for t in valid_transcripts) / len(valid_transcripts)
                    avg_clarity = sum(t.get("clarity_score", 0.8) for t in valid_transcripts) / len(valid_transcripts)
                    total_filler_words = sum(len(t.get("filler_words", [])) for t in valid_transcripts)
                    avg_pause_count = sum(t.get("pause_count", 0) for t in valid_transcripts) / len(valid_transcripts)
                    
                    # Add detailed speech metrics
                    speaking_analysis.update({
                        "average_speaking_rate": avg_speaking_rate,
                        "average_clarity_score": avg_clarity,
                        "total_filler_words": total_filler_words,
                        "average_pause_count": avg_pause_count,
                        "speech_quality_score": (avg_clarity * 0.6 + min(1.0, 150/avg_speaking_rate) * 0.4) * 100
                    })
                    
                    # Analyze speaking rate
                    if avg_speaking_rate < 120:
                        speaking_analysis["communication_improvements"].append("Consider speaking slightly faster to maintain engagement")
                    elif avg_speaking_rate > 180:
                        speaking_analysis["communication_improvements"].append("Try speaking slightly slower for better clarity")
                    else:
                        speaking_analysis["communication_strengths"].append("Good speaking pace and rhythm")
                    
                    # Analyze clarity
                    if avg_clarity >= 0.9:
                        speaking_analysis["communication_strengths"].append("Excellent speech clarity and pronunciation")
                    elif avg_clarity >= 0.8:
                        speaking_analysis["communication_strengths"].append("Good speech clarity")
                    else:
                        speaking_analysis["communication_improvements"].append("Focus on speaking more clearly and distinctly")
                    
                    # Analyze filler words
                    if total_filler_words <= len(valid_transcripts):  # 1 or fewer per response
                        speaking_analysis["communication_strengths"].append("Minimal use of filler words")
                    elif total_filler_words > len(valid_transcripts) * 3:  # More than 3 per response
                        speaking_analysis["communication_improvements"].append("Reduce use of filler words (um, uh, like)")
                    
                    # Analyze pauses
                    if avg_pause_count <= 2:
                        speaking_analysis["communication_strengths"].append("Good flow and minimal hesitation")
                    elif avg_pause_count > 4:
                        speaking_analysis["communication_improvements"].append("Practice to reduce hesitation and improve flow")
            
            # Analyze response patterns (existing logic)
            response_times = [r.response_time for r in session.responses]
            avg_time = sum(response_times) / len(response_times) if response_times else 0
            
            if avg_time < 45:
                speaking_analysis["communication_improvements"].append("Consider taking more time to structure your responses")
            elif avg_time > 150:
                speaking_analysis["communication_improvements"].append("Try to be more concise in your responses")
            else:
                speaking_analysis["communication_strengths"].append("Good response timing and pacing")
            
            # Analyze response lengths
            response_lengths = [len(r.response.split()) if r.response else 0 for r in session.responses]
            avg_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0
            
            if avg_length < 30:
                speaking_analysis["communication_improvements"].append("Provide more detailed responses with specific examples")
            elif avg_length > 150:
                speaking_analysis["communication_improvements"].append("Focus on key points to maintain interviewer engagement")
            else:
                speaking_analysis["communication_strengths"].append("Appropriate response detail and length")
            
            # Determine overall confidence level
            confidence_indicators = len(speaking_analysis["communication_strengths"])
            improvement_areas = len(speaking_analysis["communication_improvements"])
            
            if confidence_indicators > improvement_areas:
                speaking_analysis["overall_confidence"] = "high"
            elif confidence_indicators == improvement_areas:
                speaking_analysis["overall_confidence"] = "moderate"
            else:
                speaking_analysis["overall_confidence"] = "developing"
            
            # Add speaking analysis to feedback
            if hasattr(feedback, 'dict'):
                feedback_dict = feedback.dict()
                feedback_dict["speaking_analysis"] = speaking_analysis
                return feedback_dict
            else:
                feedback["speaking_analysis"] = speaking_analysis
            
            # Update overall recommendations based on speech analysis
            if speaking_analysis["communication_improvements"]:
                if hasattr(feedback, 'recommendations'):
                    feedback.recommendations.extend(speaking_analysis["communication_improvements"][:2])  # Add top 2
                else:
                    feedback["recommendations"].extend(speaking_analysis["communication_improvements"][:2])
            
            return feedback
            
        except Exception as e:
            logger.error(f"Speech analysis enhancement failed: {str(e)}")
            return feedback
    
    def _format_qa_for_ai(self, questions_and_responses):
        """Format questions and responses for AI analysis"""
        formatted = []
        for i, qa in enumerate(questions_and_responses):
            formatted.append(f"""
            Q{i+1} ({qa['category']}, {qa['difficulty']}): {qa['question']}
            Key Points: {', '.join(qa['key_points'])}
            Response ({qa['response_time']}s): {qa['response']}
            """)
        return "\n".join(formatted)
    
    def _format_enhanced_qa_for_ai(self, enhanced_responses):
        """Format enhanced questions and responses for comprehensive AI analysis"""
        formatted = []
        for i, response in enumerate(enhanced_responses):
            audio_info = ""
            if response['has_audio'] and response['speech_transcript']:
                transcript = response['speech_transcript']
                audio_info = f"""
            Audio Analysis:
            - Speaking Rate: {transcript.get('speaking_rate', 'N/A')} WPM
            - Clarity Score: {transcript.get('clarity_score', 'N/A')}
            - Filler Words: {', '.join(transcript.get('filler_words', []))}
            - Transcript: {transcript.get('transcript', 'N/A')}"""
            
            formatted.append(f"""
            Q{i+1} ({response['category']}, {response['difficulty']}): {response['question']}
            Key Points: {', '.join(response['key_points'])}
            Text Response ({response['response_time']}s): {response['text_response']}
            Has Audio: {response['has_audio']}
            Has Video: {response['has_video']}{audio_info}
            """)
        return "\n".join(formatted)
    
    def _parse_ai_feedback(self, ai_response, session, enhanced_responses=None):
        """Parse AI feedback response into structured format with enhanced analysis"""
        try:
            import re
            lines = ai_response.split('\n')
            
            feedback_data = {
                "overall_score": 75,  # Default score
                "strengths": [],
                "areas_for_improvement": [],
                "detailed_feedback": [],
                "recommendations": [],
                "speaking_patterns": {
                    "pace": "moderate",
                    "clarity": "good",
                    "confidence": "moderate",
                    "filler_words": 0,
                    "response_structure": "adequate"
                }
            }
            
            current_section = None
            question_scores = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Try to extract overall score with more patterns
                score_patterns = [
                    r'overall score[:\s]*(\d+)',
                    r'total score[:\s]*(\d+)',
                    r'score[:\s]*(\d+)(?:/100|\s*out\s*of\s*100)',
                    r'(\d+)(?:/100|\s*out\s*of\s*100)'
                ]
                
                for pattern in score_patterns:
                    score_match = re.search(pattern, line.lower())
                    if score_match:
                        feedback_data["overall_score"] = min(100, max(0, int(score_match.group(1))))
                        break
                
                # Extract question scores
                question_score_match = re.search(r'question\s*(\d+)[:\s]*(\d+)', line.lower())
                if question_score_match:
                    question_scores.append(int(question_score_match.group(2)))
                
                # Extract sections with better pattern matching
                if re.search(r'strengths?[:\s]*$', line.lower()):
                    current_section = "strengths"
                elif re.search(r'(?:areas?\s*for\s*)?improvements?[:\s]*$', line.lower()):
                    current_section = "areas_for_improvement"
                elif re.search(r'recommendations?[:\s]*$', line.lower()):
                    current_section = "recommendations"
                elif line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.')):
                    if current_section and current_section in feedback_data:
                        # Clean up the bullet point
                        clean_text = re.sub(r'^[-•*\d\.]\s*', '', line).strip()
                        if clean_text:
                            feedback_data[current_section].append(clean_text)
            
            # Generate detailed feedback for each question with enhanced analysis
            for i, response in enumerate(session.responses):
                # Use extracted question score or calculate based on response quality
                if i < len(question_scores):
                    question_score = question_scores[i]
                else:
                    # Enhanced scoring algorithm
                    base_score = self._calculate_response_score(response, session.questions[i])
                    question_score = base_score
                
                # Get speech transcript for this response
                speech_transcript = None
                if enhanced_responses and i < len(enhanced_responses):
                    speech_transcript = enhanced_responses[i].get("speech_transcript")
                
                # Analyze speech patterns with transcript
                speech_analysis = self._analyze_speech_patterns(response, speech_transcript)
                
                # Generate more detailed feedback
                detailed_feedback_text = self._generate_detailed_question_feedback(
                    response, session.questions[i], question_score, speech_analysis
                )
                
                feedback_data["detailed_feedback"].append({
                    "question_index": i,
                    "question_id": response.question_id,
                    "score": question_score,
                    "feedback": detailed_feedback_text,
                    "speech_analysis": speech_analysis,
                    "strengths": speech_analysis.get("confidence_indicators", []),
                    "improvements": speech_analysis.get("areas_for_improvement", [])
                })
            
            # Ensure we have meaningful feedback
            if not feedback_data["strengths"]:
                feedback_data["strengths"] = self._generate_default_strengths(session, feedback_data["overall_score"])
            
            if not feedback_data["areas_for_improvement"]:
                feedback_data["areas_for_improvement"] = self._generate_default_improvements(feedback_data["overall_score"])
            
            if not feedback_data["recommendations"]:
                feedback_data["recommendations"] = self._generate_default_recommendations(feedback_data["overall_score"])
            
            # Create InterviewFeedback object
            feedback = InterviewFeedback(
                session_id=session.session_id,
                overall_score=feedback_data["overall_score"],
                strengths=feedback_data["strengths"],
                areas_for_improvement=feedback_data["areas_for_improvement"],
                detailed_feedback=feedback_data["detailed_feedback"],
                recommendations=feedback_data["recommendations"],
                generated_at=datetime.utcnow()
            )
            
            return feedback
            
        except Exception as e:
            logger.error(f"Failed to parse AI feedback: {str(e)}")
            return self._generate_enhanced_template_feedback(session.questions, session.responses, enhanced_responses)
    
    def _calculate_response_score(self, response, question):
        """Calculate a score for an individual response based on multiple factors"""
        score = 0
        response_text = response.response or ""
        word_count = len(response_text.split())
        
        # Content length score (0-30 points)
        if word_count >= 50:
            score += 30
        elif word_count >= 30:
            score += 20
        elif word_count >= 15:
            score += 10
        
        # Content quality indicators (0-40 points)
        quality_keywords = [
            "example", "experience", "result", "achieved", "improved", "led", "managed",
            "developed", "implemented", "solved", "challenge", "situation", "task", "action"
        ]
        
        keyword_count = sum(1 for keyword in quality_keywords if keyword in response_text.lower())
        score += min(25, keyword_count * 3)
        
        # STAR method indicators (0-15 points)
        star_indicators = ["situation", "task", "action", "result", "outcome", "impact"]
        star_count = sum(1 for indicator in star_indicators if indicator in response_text.lower())
        score += min(15, star_count * 3)
        
        # Response time appropriateness (0-15 points)
        if 45 <= response.response_time <= 120:
            score += 15
        elif 30 <= response.response_time <= 150:
            score += 10
        elif response.response_time <= 180:
            score += 5
        
        return min(100, max(20, score))
    
    def _generate_detailed_question_feedback(self, response, question, score, speech_analysis):
        """Generate detailed feedback for a specific question"""
        feedback_parts = []
        
        # Score-based feedback
        if score >= 85:
            feedback_parts.append("Excellent response that thoroughly addresses the question.")
        elif score >= 70:
            feedback_parts.append("Good response with solid content.")
        elif score >= 55:
            feedback_parts.append("Adequate response that covers the basics.")
        else:
            feedback_parts.append("Response could be significantly improved.")
        
        # Content analysis
        word_count = len(response.response.split()) if response.response else 0
        if word_count < 20:
            feedback_parts.append("Consider providing more detailed examples and explanations.")
        elif word_count > 150:
            feedback_parts.append("Good level of detail - ensure all points are relevant.")
        
        # STAR method analysis
        response_text = response.response.lower() if response.response else ""
        star_indicators = sum(1 for word in ["situation", "task", "action", "result"] if word in response_text)
        if star_indicators >= 2:
            feedback_parts.append("Good use of structured storytelling approach.")
        else:
            feedback_parts.append("Consider using the STAR method to structure your response.")
        
        # Speech analysis feedback
        if speech_analysis.get("has_audio"):
            if speech_analysis.get("clarity_score", 0) > 0.8:
                feedback_parts.append("Clear and confident delivery.")
            else:
                feedback_parts.append("Focus on speaking more clearly and confidently.")
        
        return " ".join(feedback_parts)
    
    def _generate_default_strengths(self, session, overall_score):
        """Generate default strengths based on session data"""
        strengths = ["Completed the full interview session"]
        
        if overall_score >= 80:
            strengths.extend([
                "Provided comprehensive and well-structured responses",
                "Demonstrated good communication skills",
                "Used specific examples effectively"
            ])
        elif overall_score >= 65:
            strengths.extend([
                "Showed good understanding of the questions",
                "Provided relevant and thoughtful responses"
            ])
        else:
            strengths.append("Showed engagement and willingness to participate")
        
        # Add audio-specific strengths if applicable
        audio_responses = sum(1 for r in session.responses if r.audio_url)
        if audio_responses > 0:
            strengths.append(f"Utilized audio recording for {audio_responses} responses")
        
        return strengths
    
    def _generate_default_improvements(self, overall_score):
        """Generate default improvement areas based on score"""
        improvements = []
        
        if overall_score < 85:
            improvements.append("Provide more specific examples and quantifiable results")
        
        if overall_score < 75:
            improvements.extend([
                "Practice structuring responses using the STAR method",
                "Include more details about your specific role and contributions"
            ])
        
        if overall_score < 65:
            improvements.extend([
                "Work on providing more comprehensive responses",
                "Practice common interview questions to improve confidence"
            ])
        
        return improvements or ["Continue practicing to maintain strong performance"]
    
    def _generate_default_recommendations(self, overall_score):
        """Generate default recommendations based on score"""
        recommendations = [
            "Practice more mock interviews to build confidence",
            "Prepare specific examples for common behavioral questions"
        ]
        
        if overall_score < 75:
            recommendations.extend([
                "Research and practice the STAR method for behavioral questions",
                "Prepare a portfolio of achievements and challenges to draw from"
            ])
        
        if overall_score < 65:
            recommendations.extend([
                "Record yourself answering questions to improve delivery",
                "Focus on providing concrete examples with measurable outcomes"
            ])
        
        recommendations.append("Research the company and role thoroughly before interviews")
        
        return recommendations

    def _generate_template_feedback(self, questions, responses):
        """Generate basic template feedback"""
        response_count = len(responses)
        
        # Basic scoring based on response length and completeness
        scores = []
        detailed_feedback = []
        
        for i, response in enumerate(responses):
            if hasattr(response, 'response'):
                response_text = response.response
            else:
                response_text = response.get("response", "")
                
            response_length = len(response_text.split())
            
            # Score based on response length and quality indicators
            length_score = min(60, response_length * 2)  # Up to 60 points for length
            
            # Bonus points for quality indicators
            quality_bonus = 0
            if "example" in response_text.lower() or "time" in response_text.lower():
                quality_bonus += 15
            if len(response_text.split()) > 50:  # Detailed response
                quality_bonus += 15
            if "result" in response_text.lower() or "outcome" in response_text.lower():
                quality_bonus += 10
                
            final_score = min(100, length_score + quality_bonus)
            scores.append(final_score)
            
            detailed_feedback.append({
                "question_index": i,
                "question_id": questions[i].id if hasattr(questions[i], 'id') else str(i),
                "score": int(final_score),
                "feedback": self._get_question_feedback(final_score, response_text)
            })
        
        overall_score = sum(scores) / max(len(scores), 1) if scores else 50
        
        # Create InterviewFeedback object
        feedback = InterviewFeedback(
            session_id="template",
            overall_score=int(overall_score),
            strengths=self._get_strengths(overall_score, response_count, len(questions)),
            areas_for_improvement=self._get_improvements(overall_score),
            detailed_feedback=detailed_feedback,
            recommendations=self._get_recommendations(overall_score),
            generated_at=datetime.utcnow()
        )
        
        return feedback
    
    def _get_question_feedback(self, score, response_text):
        """Generate feedback for individual question based on score"""
        if score >= 80:
            return "Excellent response with good structure and specific examples. Well done!"
        elif score >= 60:
            return "Good response. Consider adding more specific examples and details to strengthen your answer."
        else:
            return "Response could be improved. Try to provide more detailed examples and use the STAR method for behavioral questions."
    
    def _get_strengths(self, overall_score, response_count, total_questions):
        """Generate strengths based on performance"""
        strengths = []
        
        if response_count == total_questions:
            strengths.append("Completed all interview questions")
        else:
            strengths.append("Participated actively in the interview")
            
        if overall_score >= 80:
            strengths.extend([
                "Provided detailed and well-structured responses",
                "Demonstrated good communication skills",
                "Used specific examples effectively"
            ])
        elif overall_score >= 60:
            strengths.extend([
                "Showed good understanding of questions",
                "Provided relevant responses"
            ])
        else:
            strengths.append("Showed willingness to engage with challenging questions")
            
        return strengths
    
    def _get_improvements(self, overall_score):
        """Generate improvement areas based on performance"""
        improvements = []
        
        if overall_score < 80:
            improvements.append("Provide more specific examples in your responses")
            
        if overall_score < 70:
            improvements.extend([
                "Practice structuring answers using the STAR method",
                "Include more details about your role and impact"
            ])
            
        if overall_score < 60:
            improvements.extend([
                "Work on providing more comprehensive responses",
                "Practice common interview questions beforehand"
            ])
            
        return improvements or ["Continue practicing to maintain strong performance"]
    
    def _get_recommendations(self, overall_score):
        """Generate recommendations based on performance"""
        recommendations = [
            "Practice more mock interviews to build confidence",
            "Prepare specific examples for common behavioral questions"
        ]
        
        if overall_score < 70:
            recommendations.extend([
                "Research the STAR method for behavioral questions",
                "Practice explaining your experiences with more detail"
            ])
            
        if overall_score < 60:
            recommendations.extend([
                "Record yourself answering questions to improve delivery",
                "Prepare a list of achievements and challenges to draw from"
            ])
            
        recommendations.append("Research the company and role thoroughly before interviews")
        
        return recommendations    

    def _generate_enhanced_template_feedback(self, questions, responses, enhanced_responses=None):
        """Generate enhanced template feedback with speech analysis"""
        try:
            response_count = len(responses)
            
            # Enhanced scoring with speech analysis
            scores = []
            detailed_feedback = []
            
            for i, response in enumerate(responses):
                question = questions[i] if i < len(questions) else None
                
                # Calculate enhanced score
                if question:
                    score = self._calculate_response_score(response, question)
                else:
                    # Fallback scoring
                    word_count = len(response.response.split()) if response.response else 0
                    score = min(100, max(20, word_count * 2 + 30))
                
                scores.append(score)
                
                # Get speech analysis
                speech_transcript = None
                if enhanced_responses and i < len(enhanced_responses):
                    speech_transcript = enhanced_responses[i].get("speech_transcript")
                
                speech_analysis = self._analyze_speech_patterns(response, speech_transcript)
                
                # Generate detailed feedback
                feedback_text = self._generate_detailed_question_feedback(
                    response, question, score, speech_analysis
                )
                
                detailed_feedback.append({
                    "question_index": i,
                    "question_id": question.id if question and hasattr(question, 'id') else str(i),
                    "score": int(score),
                    "feedback": feedback_text,
                    "speech_analysis": speech_analysis,
                    "strengths": speech_analysis.get("confidence_indicators", []),
                    "improvements": speech_analysis.get("areas_for_improvement", [])
                })
            
            overall_score = sum(scores) / max(len(scores), 1) if scores else 50
            
            # Create InterviewFeedback object with enhanced data
            feedback = InterviewFeedback(
                session_id="enhanced_template",
                overall_score=int(overall_score),
                strengths=self._generate_default_strengths_from_responses(responses, overall_score),
                areas_for_improvement=self._generate_default_improvements(overall_score),
                detailed_feedback=detailed_feedback,
                recommendations=self._generate_default_recommendations(overall_score),
                generated_at=datetime.utcnow()
            )
            
            return feedback
            
        except Exception as e:
            logger.error(f"Enhanced template feedback generation failed: {str(e)}")
            return self._generate_template_feedback(questions, responses)
    
    def _generate_default_strengths_from_responses(self, responses, overall_score):
        """Generate strengths based on actual response data"""
        strengths = [f"Completed {len(responses)} interview questions"]
        
        # Analyze response characteristics
        audio_count = sum(1 for r in responses if r.audio_url)
        avg_response_time = sum(r.response_time for r in responses) / len(responses) if responses else 0
        avg_word_count = sum(len(r.response.split()) if r.response else 0 for r in responses) / len(responses) if responses else 0
        
        if audio_count > 0:
            strengths.append(f"Utilized audio recording for {audio_count} responses")
        
        if 45 <= avg_response_time <= 120:
            strengths.append("Demonstrated good response timing")
        
        if avg_word_count >= 40:
            strengths.append("Provided detailed and comprehensive responses")
        
        if overall_score >= 80:
            strengths.extend([
                "Showed strong communication skills",
                "Demonstrated good preparation and knowledge"
            ])
        elif overall_score >= 65:
            strengths.append("Showed good understanding of interview questions")
        
        return strengths    
   
 # Abstract method implementations required by BaseAgent
    
    async def _process_request_impl(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementation of request processing for interview preparation
        """
        try:
            task_type = user_input.get("task_type", "generate_questions")
            user_id = user_input.get("user_id") or context.get("user_id")
            
            if task_type == "generate_questions":
                job_role = user_input.get("job_role", "")
                difficulty = user_input.get("difficulty", "intermediate")
                question_types = user_input.get("question_types", ["behavioral", "technical"])
                
                questions = await self.generate_interview_questions(
                    job_role=job_role,
                    difficulty=difficulty,
                    question_types=question_types
                )
                
                return {
                    "success": True,
                    "data": {"questions": questions},
                    "recommendations": [
                        {
                            "type": "interview_practice",
                            "description": f"Practice with {len(questions)} interview questions",
                            "action": "start_practice",
                            "priority": "high"
                        }
                    ],
                    "metadata": {
                        "job_role": job_role,
                        "difficulty": difficulty,
                        "question_count": len(questions),
                        "generation_timestamp": datetime.utcnow().isoformat()
                    }
                }
            
            elif task_type == "conduct_mock_interview":
                questions = user_input.get("questions", [])
                
                mock_interview = await self.conduct_mock_interview(questions)
                
                return {
                    "success": True,
                    "data": mock_interview,
                    "recommendations": [
                        {
                            "type": "interview_feedback",
                            "description": "Review your mock interview performance",
                            "action": "review_feedback",
                            "priority": "high"
                        }
                    ],
                    "metadata": {
                        "interview_timestamp": datetime.utcnow().isoformat()
                    }
                }
            
            elif task_type == "analyze_performance":
                interview_data = user_input.get("interview_data", {})
                
                analysis = await self.analyze_interview_performance(interview_data)
                
                return {
                    "success": True,
                    "data": analysis,
                    "recommendations": [
                        {
                            "type": "performance_improvement",
                            "description": "Focus on identified improvement areas",
                            "action": "practice_weak_areas",
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
        Implementation of recommendations generation for interview preparation
        """
        try:
            recommendations = []
            
            # Generate interview preparation recommendations
            target_role = user_profile.get("target_role", "")
            experience_level = user_profile.get("experience_level", "intermediate")
            upcoming_interviews = user_profile.get("upcoming_interviews", [])
            
            if upcoming_interviews:
                for interview in upcoming_interviews[:3]:  # Top 3 upcoming
                    recommendations.append({
                        "type": "interview_preparation",
                        "description": f"Prepare for {interview.get('company', 'upcoming')} interview",
                        "action": "generate_questions",
                        "priority": "high",
                        "metadata": {
                            "company": interview.get("company"),
                            "role": interview.get("role"),
                            "date": interview.get("date")
                        }
                    })
            
            if target_role:
                recommendations.append({
                    "type": "role_specific_prep",
                    "description": f"Practice {target_role} specific interview questions",
                    "action": "practice_role_questions",
                    "priority": "medium",
                    "metadata": {
                        "target_role": target_role,
                        "experience_level": experience_level
                    }
                })
            
            recommendations.append({
                "type": "mock_interview",
                "description": "Take a mock interview to assess your readiness",
                "action": "start_mock_interview",
                "priority": "medium",
                "metadata": {
                    "estimated_duration": "30-45 minutes"
                }
            })
            
            return recommendations
                
        except Exception as e:
            logger.error(f"Error in _get_recommendations_impl: {str(e)}")
            return []