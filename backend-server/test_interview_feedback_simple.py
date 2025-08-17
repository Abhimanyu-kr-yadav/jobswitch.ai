#!/usr/bin/env python3
"""
Simple test for enhanced interview feedback system
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.agents.interview_preparation import InterviewPreparationAgent
from app.models.interview import (
    InterviewSession, InterviewQuestion, InterviewResponse, 
    InterviewQuestionCategory, InterviewQuestionDifficulty, InterviewSessionStatus
)


async def test_feedback_system():
    """Test the enhanced feedback system"""
    print("🎯 Testing Enhanced Interview Feedback System")
    print("=" * 50)
    
    # Initialize agent
    agent = InterviewPreparationAgent()
    
    # Create test session
    session_id = "test_enhanced"
    
    questions = [
        InterviewQuestion(
            id="q1",
            question="Tell me about a challenging project you worked on.",
            category=InterviewQuestionCategory.BEHAVIORAL,
            difficulty=InterviewQuestionDifficulty.MEDIUM,
            time_limit=120,
            key_points=["Challenge", "Actions", "Results"],
            answer_structure="Use STAR method"
        )
    ]
    
    responses = [
        InterviewResponse(
            question_id="q1",
            response="In my previous role, I led a team to migrate our legacy system to microservices. The challenge was ensuring zero downtime. I developed a phased approach, implemented monitoring, and created rollback procedures. We achieved 99.9% uptime and 40% performance improvement.",
            response_time=85,
            audio_url="/uploads/test_audio.webm",
            video_url=None,
            timestamp=datetime.utcnow()
        )
    ]
    
    session = InterviewSession(
        session_id=session_id,
        user_id="test_user",
        job_role="Software Engineer",
        company="TechCorp",
        questions=questions,
        responses=responses,
        current_question_index=1,
        status=InterviewSessionStatus.COMPLETED,
        recording_mode="audio",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    
    agent.active_sessions[session_id] = session
    
    print("✅ Created test session")
    
    # Test speech-to-text
    print("\n🎤 Testing Speech-to-Text Processing")
    transcript = await agent._process_speech_to_text("/uploads/test_audio.webm")
    if transcript:
        print(f"✅ Speech processing successful")
        print(f"   - Speaking Rate: {transcript.get('speaking_rate', 'N/A')} WPM")
        print(f"   - Clarity Score: {transcript.get('clarity_score', 'N/A')}")
        print(f"   - Filler Words: {transcript.get('filler_words', [])}")
    
    # Test feedback generation
    print("\n🧠 Testing Feedback Generation")
    user_input = {"action": "get_feedback", "session_id": session_id}
    context = {"user_id": "test_user"}
    
    result = await agent.process_request(user_input, context)
    
    if result.get("success"):
        feedback = result["data"]["feedback"]
        print("✅ Feedback generation successful")
        print(f"   - Overall Score: {feedback.get('overall_score', 'N/A')}/100")
        print(f"   - Strengths: {len(feedback.get('strengths', []))}")
        print(f"   - Improvements: {len(feedback.get('areas_for_improvement', []))}")
        print(f"   - Recommendations: {len(feedback.get('recommendations', []))}")
        
        # Check speaking analysis
        speaking_analysis = feedback.get('speaking_analysis')
        if speaking_analysis:
            print("   - Speaking Analysis: ✅ Available")
            print(f"     • Audio Responses: {speaking_analysis.get('audio_responses', 'N/A')}")
            print(f"     • Overall Confidence: {speaking_analysis.get('overall_confidence', 'N/A')}")
        
        # Check detailed feedback
        detailed = feedback.get('detailed_feedback', [])
        if detailed:
            item = detailed[0]
            print(f"   - Question 1 Score: {item.get('score', 'N/A')}/100")
            speech_analysis = item.get('speech_analysis', {})
            if speech_analysis.get('has_audio'):
                print(f"     • Has Audio Analysis: ✅")
                print(f"     • Response Time: {speech_analysis.get('response_time', 'N/A')}s")
                print(f"     • Clarity Score: {speech_analysis.get('clarity_score', 'N/A')}")
        
        print("\n🎉 All tests passed! Enhanced feedback system is working.")
        return True
    else:
        print(f"❌ Feedback generation failed: {result.get('error', 'Unknown error')}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_feedback_system())
    if not success:
        sys.exit(1)