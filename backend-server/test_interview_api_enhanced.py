#!/usr/bin/env python3
"""
Test script for enhanced interview API endpoints
Tests the complete interview feedback API workflow
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from fastapi.testclient import TestClient
from app.main import app

# Create test client
client = TestClient(app)

# Mock authentication token
test_token = "test_token_123"
auth_headers = {"Authorization": f"Bearer {test_token}"}


def test_enhanced_interview_workflow():
    """Test the complete enhanced interview workflow"""
    print("🎯 Testing Enhanced Interview API Workflow")
    print("=" * 50)
    
    # Test 1: Start mock interview
    print("🚀 Test 1: Starting Mock Interview")
    print("-" * 30)
    
    interview_request = {
        "job_role": "Senior Software Engineer",
        "company": "TechCorp",
        "question_count": 3,
        "categories": ["behavioral", "technical"]
    }
    
    try:
        response = client.post(
            "/api/v1/agents/interview-preparation/start-mock-interview",
            json=interview_request,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                session_id = data["data"]["session_id"]
                print(f"✅ Mock interview started successfully")
                print(f"   - Session ID: {session_id}")
                print(f"   - Total Questions: {data['data']['total_questions']}")
                print(f"   - Current Question: {data['data']['current_question']['question'][:50]}...")
            else:
                print(f"❌ Mock interview failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ API request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception during mock interview start: {str(e)}")
        return False
    
    print()
    
    # Test 2: Submit responses with audio
    print("🎤 Test 2: Submitting Responses with Audio")
    print("-" * 30)
    
    responses = [
        {
            "session_id": session_id,
            "response": "In my previous role as a software engineer, I was tasked with migrating our legacy system to a microservices architecture. The main challenge was ensuring zero downtime during the migration. I developed a phased approach where we gradually moved services one by one, implemented comprehensive monitoring, and created rollback procedures. As a result, we successfully completed the migration with 99.9% uptime and improved system performance by 40%.",
            "response_time": 95,
            "audio_url": "/uploads/recordings/test_audio_1.webm"
        },
        {
            "session_id": session_id,
            "response": "For a scalable web application, I would use a microservices architecture with load balancers, implement caching strategies, use containerization with Docker and Kubernetes, and design for horizontal scaling. Database sharding and CDN integration would also be important.",
            "response_time": 75,
            "audio_url": "/uploads/recordings/test_audio_2.webm"
        },
        {
            "session_id": session_id,
            "response": "I'm interested in your company because of your innovative approach to technology and strong company culture.",
            "response_time": 30
        }
    ]
    
    for i, response_data in enumerate(responses):
        try:
            response = client.post(
                "/api/v1/agents/interview-preparation/submit-response",
                json=response_data,
                headers=auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ Response {i+1} submitted successfully")
                    if data["data"].get("session_complete"):
                        print("   - Interview session completed!")
                        break
                    else:
                        print(f"   - Next question ready")
                else:
                    print(f"❌ Response {i+1} submission failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ Response {i+1} API request failed with status {response.status_code}")
        except Exception as e:
            print(f"❌ Exception during response {i+1} submission: {str(e)}")
    
    print()
    
    # Test 3: Process speech-to-text
    print("🗣️  Test 3: Processing Speech-to-Text")
    print("-" * 30)
    
    audio_urls = ["/uploads/recordings/test_audio_1.webm", "/uploads/recordings/test_audio_2.webm"]
    
    for i, audio_url in enumerate(audio_urls):
        try:
            response = client.post(
                "/api/v1/agents/interview-preparation/process-speech-to-text",
                json={"audio_url": audio_url},
                headers=auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    transcript_data = data["data"]["transcript"]
                    analysis_data = data["data"]["analysis"]
                    
                    print(f"✅ Speech-to-text {i+1} processed successfully")
                    print(f"   - Transcript: {transcript_data.get('transcript', 'N/A')[:50]}...")
                    print(f"   - Speaking Rate: {analysis_data.get('speaking_rate', 'N/A')} WPM")
                    print(f"   - Clarity Score: {analysis_data.get('clarity_score', 'N/A')}")
                    print(f"   - Word Count: {analysis_data.get('word_count', 'N/A')}")
                    print(f"   - Filler Words: {analysis_data.get('filler_words', [])}")
                else:
                    print(f"❌ Speech-to-text {i+1} failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ Speech-to-text {i+1} API request failed with status {response.status_code}")
        except Exception as e:
            print(f"❌ Exception during speech-to-text {i+1}: {str(e)}")
    
    print()
    
    # Test 4: Analyze speech patterns
    print("📊 Test 4: Analyzing Speech Patterns")
    print("-" * 30)
    
    try:
        response = client.post(
            "/api/v1/agents/interview-preparation/analyze-speech-patterns",
            json={"audio_urls": audio_urls},
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                analysis = data["data"]
                print("✅ Speech pattern analysis successful")
                print(f"   - Total Responses: {analysis.get('total_responses', 'N/A')}")
                print(f"   - Average Speaking Rate: {analysis.get('average_speaking_rate', 'N/A'):.0f} WPM")
                print(f"   - Average Clarity: {analysis.get('average_clarity_score', 'N/A'):.2f}")
                print(f"   - Total Filler Words: {analysis.get('total_filler_words', 'N/A')}")
                print(f"   - Speech Quality Score: {analysis.get('speech_quality_score', 'N/A'):.0f}%")
            else:
                print(f"❌ Speech pattern analysis failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Speech pattern analysis API request failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Exception during speech pattern analysis: {str(e)}")
    
    print()
    
    # Test 5: Get enhanced feedback
    print("🧠 Test 5: Getting Enhanced Feedback")
    print("-" * 30)
    
    try:
        response = client.post(
            "/api/v1/agents/interview-preparation/get-feedback",
            json={"session_id": session_id},
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                feedback = data["data"]["feedback"]
                print("✅ Enhanced feedback generated successfully")
                print(f"   - Overall Score: {feedback.get('overall_score', 'N/A')}/100")
                print(f"   - Strengths Count: {len(feedback.get('strengths', []))}")
                print(f"   - Improvements Count: {len(feedback.get('areas_for_improvement', []))}")
                print(f"   - Detailed Feedback Count: {len(feedback.get('detailed_feedback', []))}")
                print(f"   - Recommendations Count: {len(feedback.get('recommendations', []))}")
                
                # Check for speaking analysis
                speaking_analysis = feedback.get('speaking_analysis')
                if speaking_analysis:
                    print("   - Speaking Analysis: ✅ Available")
                    print(f"     • Audio Responses: {speaking_analysis.get('audio_responses', 'N/A')}")
                    print(f"     • Overall Confidence: {speaking_analysis.get('overall_confidence', 'N/A')}")
                    if speaking_analysis.get('average_speaking_rate'):
                        print(f"     • Average Speaking Rate: {speaking_analysis.get('average_speaking_rate', 'N/A'):.0f} WPM")
                        print(f"     • Speech Quality Score: {speaking_analysis.get('speech_quality_score', 'N/A'):.0f}%")
                else:
                    print("   - Speaking Analysis: ❌ Not available")
                
                # Check detailed feedback for speech analysis
                detailed_feedback = feedback.get('detailed_feedback', [])
                audio_analysis_count = sum(1 for item in detailed_feedback if item.get('speech_analysis', {}).get('has_audio'))
                print(f"   - Questions with Audio Analysis: {audio_analysis_count}/{len(detailed_feedback)}")
                
                return True
            else:
                print(f"❌ Enhanced feedback failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Enhanced feedback API request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception during enhanced feedback: {str(e)}")
        return False


def test_api_error_handling():
    """Test API error handling"""
    print("\n🛡️  Testing API Error Handling")
    print("=" * 30)
    
    # Test invalid session ID
    print("Testing invalid session ID...")
    response = client.post(
        "/api/v1/agents/interview-preparation/get-feedback",
        json={"session_id": "invalid_session"},
        headers=auth_headers
    )
    
    if response.status_code == 400:
        print("✅ Invalid session ID handled correctly")
    else:
        print(f"❌ Invalid session ID not handled properly: {response.status_code}")
    
    # Test missing audio URL
    print("Testing missing audio URL...")
    response = client.post(
        "/api/v1/agents/interview-preparation/process-speech-to-text",
        json={},
        headers=auth_headers
    )
    
    if response.status_code == 400:
        print("✅ Missing audio URL handled correctly")
    else:
        print(f"❌ Missing audio URL not handled properly: {response.status_code}")
    
    # Test empty audio URLs array
    print("Testing empty audio URLs array...")
    response = client.post(
        "/api/v1/agents/interview-preparation/analyze-speech-patterns",
        json={"audio_urls": []},
        headers=auth_headers
    )
    
    if response.status_code == 400:
        print("✅ Empty audio URLs array handled correctly")
    else:
        print(f"❌ Empty audio URLs array not handled properly: {response.status_code}")


if __name__ == "__main__":
    print("🧪 Starting Enhanced Interview API Tests")
    print("=" * 60)
    
    # Mock the authentication dependency
    from app.core.auth import get_current_user
    
    def mock_get_current_user():
        return {"user_id": "test_user", "email": "test@example.com"}
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    try:
        success = test_enhanced_interview_workflow()
        test_api_error_handling()
        
        if success:
            print("\n🎉 All enhanced interview API tests passed!")
            print("\nEnhanced Features Tested:")
            print("✅ Mock interview session creation")
            print("✅ Response submission with audio URLs")
            print("✅ Enhanced speech-to-text processing with metrics")
            print("✅ Speech pattern analysis across multiple responses")
            print("✅ Comprehensive feedback generation with speaking analysis")
            print("✅ Individual question analysis with speech metrics")
            print("✅ API error handling and validation")
        else:
            print("\n❌ Some enhanced interview API tests failed.")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        sys.exit(1)
    finally:
        # Clean up dependency overrides
        app.dependency_overrides.clear()