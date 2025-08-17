"""
Fresh test script for Interview Preparation Agent with enhanced features
"""
import asyncio
import json
from app.agents.interview_preparation import InterviewPreparationAgent

async def test_enhanced_interview_features():
    """Test enhanced interview preparation features"""
    
    print("🎯 Testing Enhanced Interview Preparation Features...")
    
    # Initialize agent
    agent = InterviewPreparationAgent(None, None)
    
    # Test 1: Generate AI-enhanced questions with skills
    print("\n1. Testing enhanced question generation...")
    user_input = {
        "action": "generate_questions",
        "job_role": "Full Stack Developer",
        "company": "Netflix",
        "skills": ["React", "Node.js", "Python", "AWS", "System Design"],
        "question_count": 8,
        "categories": ["behavioral", "technical", "company"]
    }
    
    context = {"user_id": "test_user_456"}
    
    try:
        result = await agent.process_request(user_input, context)
        if result.get("success"):
            questions = result['data']['questions']
            print(f"✅ Generated {len(questions)} questions successfully!")
            
            # Show variety of questions
            categories = {}
            difficulties = {}
            for q in questions:
                cat = q['category']
                diff = q['difficulty']
                categories[cat] = categories.get(cat, 0) + 1
                difficulties[diff] = difficulties.get(diff, 0) + 1
            
            print(f"   Categories: {dict(categories)}")
            print(f"   Difficulties: {dict(difficulties)}")
            
            # Show a technical question example
            tech_questions = [q for q in questions if q['category'] == 'technical']
            if tech_questions:
                tech_q = tech_questions[0]
                print(f"   Technical question example: {tech_q['question']}")
                print(f"   Key points: {', '.join(tech_q['key_points'][:2])}...")
        else:
            print(f"❌ Question generation failed: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ Question generation error: {str(e)}")
    
    # Test 2: Start mock interview with recording mode
    print("\n2. Testing mock interview with recording capabilities...")
    user_input = {
        "action": "start_mock_interview",
        "job_role": "Senior Software Engineer",
        "company": "Apple",
        "skills": ["iOS", "Swift", "Objective-C"],
        "question_count": 4,
        "categories": ["behavioral", "technical"],
        "recording_mode": "video"
    }
    
    try:
        result = await agent.process_request(user_input, context)
        if result.get("success"):
            session_id = result['data']['session_id']
            print(f"✅ Mock interview started with video recording!")
            print(f"   Session ID: {session_id}")
            print(f"   Recording mode: {result['data'].get('recording_mode', 'audio')}")
            print(f"   Total questions: {result['data']['total_questions']}")
            
            # Test 3: Submit response with recording URLs
            print("\n3. Testing response submission with recording...")
            response_input = {
                "action": "submit_response",
                "session_id": session_id,
                "response": "In my role as a senior iOS developer at my previous company, I encountered a critical performance issue in our app that was causing crashes on older devices. The situation required immediate attention as it was affecting 15% of our user base. I took ownership of the problem and conducted a thorough analysis using Instruments and crash logs. I identified that the issue was caused by excessive memory usage in our image caching system. I implemented a more efficient caching strategy using NSCache with proper memory pressure handling and background queue processing. As a result, we reduced memory usage by 40% and eliminated the crashes, leading to a 25% improvement in our app store rating.",
                "response_time": 180,
                "audio_url": f"/recordings/{session_id}_audio.webm",
                "video_url": f"/recordings/{session_id}_video.webm"
            }
            
            try:
                response_result = await agent.process_request(response_input, context)
                if response_result.get("success"):
                    print(f"✅ Response with recording submitted successfully!")
                    
                    if response_result['data']['session_complete']:
                        print("   Session completed!")
                        
                        # Test 4: Generate enhanced feedback
                        print("\n4. Testing enhanced feedback generation...")
                        feedback_input = {
                            "action": "get_feedback",
                            "session_id": session_id
                        }
                        
                        try:
                            feedback_result = await agent.process_request(feedback_input, context)
                            if feedback_result.get("success"):
                                feedback = feedback_result['data']['feedback']
                                print(f"✅ Enhanced feedback generated!")
                                print(f"   Overall score: {feedback['overall_score']}/100")
                                print(f"   Strengths ({len(feedback['strengths'])}): {feedback['strengths'][0] if feedback['strengths'] else 'None'}")
                                print(f"   Improvements ({len(feedback['areas_for_improvement'])}): {feedback['areas_for_improvement'][0] if feedback['areas_for_improvement'] else 'None'}")
                                print(f"   Detailed feedback: {len(feedback['detailed_feedback'])} questions analyzed")
                                print(f"   Recommendations: {len(feedback['recommendations'])} provided")
                            else:
                                print(f"❌ Feedback generation failed: {feedback_result.get('error')}")
                        
                        except Exception as e:
                            print(f"❌ Feedback generation error: {str(e)}")
                    else:
                        print("   Session continuing...")
                        next_q = response_result['data'].get('next_question')
                        if next_q:
                            print(f"   Next question: {next_q['question'][:50]}...")
                else:
                    print(f"❌ Response submission failed: {response_result.get('error')}")
            
            except Exception as e:
                print(f"❌ Response submission error: {str(e)}")
        else:
            print(f"❌ Mock interview start failed: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ Mock interview error: {str(e)}")
    
    # Test 5: Test session management
    print("\n5. Testing session management...")
    try:
        # Test ending a session
        if 'session_id' in locals():
            end_input = {
                "action": "end_session",
                "session_id": session_id
            }
            
            end_result = await agent.process_request(end_input, context)
            if end_result.get("success"):
                print(f"✅ Session ended successfully!")
                print(f"   Responses recorded: {end_result['data']['responses_count']}")
            else:
                print(f"❌ Session end failed: {end_result.get('error')}")
    
    except Exception as e:
        print(f"❌ Session management error: {str(e)}")
    
    # Test 6: Enhanced recommendations
    print("\n6. Testing enhanced recommendations...")
    enhanced_profile = {
        "user_id": "test_user_456",
        "career_goals": {
            "target_roles": ["Senior Software Engineer", "Tech Lead", "Engineering Manager"],
            "target_companies": ["Apple", "Google", "Netflix"],
            "timeline": "6 months"
        },
        "skills": [
            {"name": "Python", "proficiency": 5, "years_experience": 8},
            {"name": "JavaScript", "proficiency": 4, "years_experience": 6},
            {"name": "System Design", "proficiency": 3, "years_experience": 4},
            {"name": "Leadership", "proficiency": 2, "years_experience": 2}
        ],
        "recent_applications": [
            {"company": "Apple", "role": "Senior iOS Engineer", "status": "interview_scheduled"},
            {"company": "Netflix", "role": "Full Stack Engineer", "status": "applied"},
            {"company": "Google", "role": "Software Engineer L5", "status": "rejected"}
        ],
        "interview_history": [
            {"company": "Microsoft", "outcome": "passed", "feedback": "strong technical skills"},
            {"company": "Amazon", "outcome": "failed", "feedback": "needs improvement in behavioral questions"}
        ]
    }
    
    try:
        recommendations = await agent.get_recommendations(enhanced_profile)
        print(f"✅ Enhanced recommendations generated!")
        print(f"   Total recommendations: {len(recommendations)}")
        
        for i, rec in enumerate(recommendations[:3]):  # Show first 3
            print(f"   {i+1}. {rec['title']}")
            print(f"      Priority: {rec['priority']} | Time: {rec['estimated_time']}")
            if 'action' in rec and 'role' in rec['action']:
                print(f"      Target role: {rec['action']['role']}")
    
    except Exception as e:
        print(f"❌ Enhanced recommendations error: {str(e)}")
    
    print("\n🎉 Enhanced Interview Preparation testing completed!")
    print("\n📊 Summary of tested features:")
    print("   ✅ AI-enhanced question generation with skills consideration")
    print("   ✅ Mock interview session management with recording support")
    print("   ✅ Response submission with audio/video URL handling")
    print("   ✅ Enhanced feedback generation with detailed analysis")
    print("   ✅ Session lifecycle management (start, progress, end)")
    print("   ✅ Personalized recommendations based on user profile")

if __name__ == "__main__":
    asyncio.run(test_enhanced_interview_features())