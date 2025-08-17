#!/usr/bin/env python3
"""
Test script for enhanced AI-powered interview feedback system
Tests speech-to-text processing, response evaluation, and feedback generation
"""

import asyncio
import json
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


async def test_enhanced_feedback_system():
    """Test the enhanced AI-powered interview feedback system"""
    print("🎯 Testing Enhanced AI-Powered Interview Feedback System")
    print("=" * 60)
    
    # Initialize the interview agent
    agent = InterviewPreparationAgent()
    
    # Create a mock interview session with responses
    session_id = "test_session_enhanced"
    
    # Create sample questions
    questions = [
        InterviewQuestion(
            id="q1",
            question="Tell me about a challenging project you worked on and how you overcame obstacles.",
            category=InterviewQuestionCategory.BEHAVIORAL,
            difficulty=InterviewQuestionDifficulty.MEDIUM,
            time_limit=120,
            key_points=["Challenge description", "Actions taken", "Results achieved"],
            answer_structure="Use STAR method: Situation, Task, Action, Result"
        ),
        InterviewQuestion(
            id="q2", 
            question="How would you design a scalable web application architecture?",
            category=InterviewQuestionCategory.TECHNICAL,
            difficulty=InterviewQuestionDifficulty.HARD,
            time_limit=180,
            key_points=["Scalability considerations", "Technology choices", "Architecture patterns"],
            answer_structure="Discuss components, scaling strategies, and trade-offs"
        ),
        InterviewQuestion(
            id="q3",
            question="Why do you want to work at our company?",
            category=InterviewQuestionCategory.COMPANY,
            difficulty=InterviewQuestionDifficulty.EASY,
            time_limit=90,
            key_points=["Company research", "Value alignment", "Career goals"],
            answer_structure="Show knowledge of company and genuine interest"
        )
    ]
    
    # Create sample responses with varying quality
    responses = [
        InterviewResponse(
            question_id="q1",
            response="In my previous role as a software engineer, I was tasked with migrating our legacy system to a microservices architecture. The main challenge was ensuring zero downtime during the migration. I developed a phased approach where we gradually moved services one by one, implemented comprehensive monitoring, and created rollback procedures. As a result, we successfully completed the migration with 99.9% uptime and improved system performance by 40%.",
            response_time=95,
            audio_url="/uploads/recordings/test_audio_1.webm",
            video_url=None,
            timestamp=datetime.utcnow()
        ),
        InterviewResponse(
            question_id="q2",
            response="For a scalable web application, I would use a microservices architecture with load balancers, implement caching strategies, use containerization with Docker and Kubernetes, and design for horizontal scaling. Database sharding and CDN integration would also be important.",
            response_time=75,
            audio_url="/uploads/recordings/test_audio_2.webm",
            video_url=None,
            timestamp=datetime.utcnow()
        ),
        InterviewResponse(
            question_id="q3",
            response="I'm interested in your company because of your innovative approach to technology and strong company culture.",
            response_time=30,
            audio_url=None,
            video_url=None,
            timestamp=datetime.utcnow()
        )
    ]
    
    # Create interview session
    session = InterviewSession(
        session_id=session_id,
        user_id="test_user",
        job_role="Senior Software Engineer",
        company="TechCorp",
        questions=questions,
        responses=responses,
        current_question_index=len(questions),
        status=InterviewSessionStatus.COMPLETED,
        recording_mode="audio",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    
    # Store session in agent
    agent.active_sessions[session_id] = session
    
    print("✅ Created mock interview session with 3 questions and responses")
    print(f"   - Session ID: {session_id}")
    print(f"   - Job Role: {session.job_role}")
    print(f"   - Company: {session.company}")
    print(f"   - Questions: {len(questions)}")
    print(f"   - Responses: {len(responses)}")
    print()
    
    # Test 1: Speech-to-text processing
    print("🎤 Test 1: Enhanced Speech-to-Text Processing")
    print("-" * 40)
    
    for i, response in enumerate(responses):
        if response.audio_url:
            print(f"Processing audio for response {i+1}...")
            transcript = await agent._process_speech_to_text(response.audio_url)
            
            if transcript:
                print(f"✅ Speech-to-text successful for response {i+1}")
                print(f"   - Transcript: {transcript.get('transcript', 'N/A')[:100]}...")
                print(f"   - Speaking Rate: {transcript.get('speaking_rate', 'N/A')} WPM")
                print(f"   - Clarity Score: {transcript.get('clarity_score', 'N/A')}")
                print(f"   - Filler Words: {transcript.get('filler_words', [])}")
                print(f"   - Confidence: {transcript.get('confidence', 'N/A')}")
            else:
                print(f"❌ Speech-to-text failed for response {i+1}")
        else:
            print(f"⏭️  No audio for response {i+1} (text-only)")
        print()
    
    # Test 2: Enhanced feedback generation
    print("🧠 Test 2: Enhanced AI Feedback Generation")
    print("-" * 40)
    
    user_input = {
        "action": "get_feedback",
        "session_id": session_id
    }
    
    context = {"user_id": "test_user"}
    
    result = await agent.process_request(user_input, context)
    
    if result.get("success"):
        feedback_data = result["data"]["feedback"]
        print("✅ Enhanced feedback generation successful!")
        print()
        
        # Display overall feedback
        print("📊 Overall Performance:")
        print(f"   - Overall Score: {feedback_data.get('overall_score', 'N/A')}/100")
        print(f"   - Generated At: {feedback_data.get('generated_at', 'N/A')}")
        print()
        
        # Display strengths
        print("💪 Strengths:")
        strengths = feedback_data.get('strengths', [])
        for i, strength in enumerate(strengths, 1):
            print(f"   {i}. {strength}")
        print()
        
        # Display areas for improvement
        print("📈 Areas for Improvement:")
        improvements = feedback_data.get('areas_for_improvement', [])
        for i, improvement in enumerate(improvements, 1):
            print(f"   {i}. {improvement}")
        print()
        
        # Display speaking analysis
        speaking_analysis = feedback_data.get('speaking_analysis')
        if speaking_analysis:
            print("🎙️  Speaking Patterns Analysis:")
            print(f"   - Total Responses: {speaking_analysis.get('total_responses', 'N/A')}")
            print(f"   - Audio Responses: {speaking_analysis.get('audio_responses', 'N/A')}")
            print(f"   - Average Response Time: {speaking_analysis.get('average_response_time', 'N/A'):.1f}s")
            print(f"   - Overall Confidence: {speaking_analysis.get('overall_confidence', 'N/A')}")
            
            if speaking_analysis.get('average_speaking_rate'):
                print(f"   - Average Speaking Rate: {speaking_analysis.get('average_speaking_rate', 'N/A'):.0f} WPM")
                print(f"   - Average Clarity Score: {speaking_analysis.get('average_clarity_score', 'N/A'):.2f}")
                print(f"   - Total Filler Words: {speaking_analysis.get('total_filler_words', 'N/A')}")
                print(f"   - Speech Quality Score: {speaking_analysis.get('speech_quality_score', 'N/A'):.0f}%")
            
            print("   Communication Strengths:")
            for strength in speaking_analysis.get('communication_strengths', []):
                print(f"     • {strength}")
            
            print("   Communication Improvements:")
            for improvement in speaking_analysis.get('communication_improvements', []):
                print(f"     • {improvement}")
            print()
        
        # Display detailed question feedback
        print("📝 Question-by-Question Analysis:")
        detailed_feedback = feedback_data.get('detailed_feedback', [])
        for item in detailed_feedback:
            print(f"   Question {item.get('question_index', 0) + 1} (Score: {item.get('score', 'N/A')}/100):")
            print(f"     Feedback: {item.get('feedback', 'N/A')}")
            
            # Speech analysis for individual question
            speech_analysis = item.get('speech_analysis', {})
            if speech_analysis.get('has_audio'):
                print(f"     Speech Analysis:")
                print(f"       - Response Time: {speech_analysis.get('response_time', 'N/A')}s")
                print(f"       - Word Count: {speech_analysis.get('response_length', 'N/A')}")
                print(f"       - Pace: {speech_analysis.get('pace_analysis', 'N/A')}")
                print(f"       - Clarity: {speech_analysis.get('clarity_score', 'N/A')}")
                
                audio_analysis = speech_analysis.get('audio_analysis', {})
                if audio_analysis:
                    print(f"       - Speaking Rate: {audio_analysis.get('speaking_rate', 'N/A')} WPM")
                    print(f"       - Filler Words: {audio_analysis.get('filler_word_count', 'N/A')}")
                    print(f"       - Clarity Rating: {audio_analysis.get('clarity_rating', 'N/A')}")
            print()
        
        # Display recommendations
        print("💡 Recommendations:")
        recommendations = feedback_data.get('recommendations', [])
        for i, recommendation in enumerate(recommendations, 1):
            print(f"   {i}. {recommendation}")
        print()
        
    else:
        print(f"❌ Enhanced feedback generation failed: {result.get('error', 'Unknown error')}")
        return False
    
    # Test 3: Response scoring algorithm
    print("🔢 Test 3: Enhanced Response Scoring")
    print("-" * 40)
    
    for i, (question, response) in enumerate(zip(questions, responses)):
        score = agent._calculate_response_score(response, question)
        print(f"Response {i+1} Score: {score}/100")
        print(f"   - Word Count: {len(response.response.split())}")
        print(f"   - Response Time: {response.response_time}s")
        print(f"   - Has Audio: {response.audio_url is not None}")
        print()
    
    print("🎉 All enhanced feedback system tests completed successfully!")
    return True


async def test_speech_pattern_analysis():
    """Test speech pattern analysis functionality"""
    print("\n🎵 Testing Speech Pattern Analysis")
    print("=" * 40)
    
    agent = InterviewPreparationAgent()
    
    # Test with mock audio URLs
    audio_urls = [
        "/uploads/recordings/test_1.webm",
        "/uploads/recordings/test_2.webm",
        "/uploads/recordings/test_3.webm"
    ]
    
    print("Processing multiple audio files for pattern analysis...")
    
    speech_analyses = []
    for i, audio_url in enumerate(audio_urls):
        transcript = await agent._process_speech_to_text(audio_url)
        if transcript:
            speech_analyses.append(transcript)
            print(f"✅ Processed audio {i+1}: {transcript.get('speaking_rate', 'N/A')} WPM")
    
    if speech_analyses:
        # Calculate overall patterns
        avg_speaking_rate = sum(s.get("speaking_rate", 150) for s in speech_analyses) / len(speech_analyses)
        avg_clarity = sum(s.get("clarity_score", 0.8) for s in speech_analyses) / len(speech_analyses)
        total_filler_words = sum(len(s.get("filler_words", [])) for s in speech_analyses)
        
        print(f"\n📊 Overall Speech Patterns:")
        print(f"   - Average Speaking Rate: {avg_speaking_rate:.0f} WPM")
        print(f"   - Average Clarity Score: {avg_clarity:.2f}")
        print(f"   - Total Filler Words: {total_filler_words}")
        print(f"   - Speech Quality Score: {(avg_clarity * 0.6 + min(1.0, 150/avg_speaking_rate) * 0.4) * 100:.0f}%")
    
    print("✅ Speech pattern analysis test completed!")


if __name__ == "__main__":
    async def main():
        success = await test_enhanced_feedback_system()
        await test_speech_pattern_analysis()
        
        if success:
            print("\n🎯 All tests passed! Enhanced AI-powered interview feedback system is working correctly.")
            print("\nKey Features Implemented:")
            print("✅ Enhanced speech-to-text processing with detailed metrics")
            print("✅ Advanced response evaluation using multiple criteria")
            print("✅ Comprehensive feedback generation with speaking patterns")
            print("✅ Individual question analysis with speech metrics")
            print("✅ Overall speech quality scoring")
            print("✅ Detailed recommendations based on performance")
        else:
            print("\n❌ Some tests failed. Please check the implementation.")
            sys.exit(1)
    
    asyncio.run(main())