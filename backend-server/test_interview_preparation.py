"""
Test script for Interview Preparation Agent
"""
import asyncio
import json
from app.agents.interview_preparation import InterviewPreparationAgent
from app.integrations.watsonx import WatsonXClient
# from app.integrations.langchain_utils import LangChainManager

async def test_interview_preparation_agent():
    """Test the interview preparation agent functionality"""
    
    print("🎯 Testing Interview Preparation Agent...")
    
    # Initialize agent (without actual WatsonX client for testing)
    agent = InterviewPreparationAgent(None, None)
    
    # Test 1: Generate questions
    print("\n1. Testing question generation...")
    user_input = {
        "action": "generate_questions",
        "job_role": "Software Engineer",
        "company": "Google",
        "skills": ["Python", "JavaScript", "System Design"],
        "question_count": 5,
        "categories": ["behavioral", "technical"]
    }
    
    context = {"user_id": "test_user_123"}
    
    try:
        result = await agent.process_request(user_input, context)
        print(f"✅ Question generation successful!")
        if 'data' in result and 'questions' in result['data']:
            print(f"   Generated {len(result['data']['questions'])} questions")
        else:
            print(f"   Result format: {result}")
        
        # Print first question as example
        if 'data' in result and 'questions' in result['data'] and result['data']['questions']:
            first_question = result['data']['questions'][0]
            print(f"   Example question: {first_question['question']}")
            print(f"   Category: {first_question['category']}")
            print(f"   Difficulty: {first_question['difficulty']}")
    
    except Exception as e:
        print(f"❌ Question generation failed: {str(e)}")
    
    # Test 2: Start mock interview
    print("\n2. Testing mock interview start...")
    user_input = {
        "action": "start_mock_interview",
        "job_role": "Product Manager",
        "company": "Microsoft",
        "question_count": 3,
        "categories": ["behavioral", "company"]
    }
    
    try:
        result = await agent.process_request(user_input, context)
        print(f"✅ Mock interview started successfully!")
        if 'data' in result and 'session_id' in result['data']:
            session_id = result['data']['session_id']
            print(f"   Session ID: {session_id}")
            print(f"   Total questions: {result['data']['total_questions']}")
            
            if result['data']['current_question']:
                print(f"   First question: {result['data']['current_question']['question']}")
        else:
            print(f"   Result format: {result}")
            session_id = None
        
        # Test 3: Submit response (only if session was created successfully)
        if session_id:
            print("\n3. Testing response submission...")
            response_input = {
                "action": "submit_response",
                "session_id": session_id,
                "response": "This is a test response using the STAR method. In my previous role as a software engineer, I faced a challenging situation where our system was experiencing performance issues. I took the initiative to analyze the problem, implemented a caching solution, and reduced response times by 50%.",
                "response_time": 120
            }
            
            try:
                response_result = await agent.process_request(response_input, context)
                print(f"✅ Response submitted successfully!")
                
                if response_result['data']['session_complete']:
                    print("   Session completed!")
                    
                    # Test 4: Get feedback
                    print("\n4. Testing feedback generation...")
                    feedback_input = {
                        "action": "get_feedback",
                        "session_id": session_id
                    }
                    
                    try:
                        feedback_result = await agent.process_request(feedback_input, context)
                        print(f"✅ Feedback generated successfully!")
                        feedback = feedback_result['data']['feedback']
                        print(f"   Overall score: {feedback['overall_score']}/100")
                        print(f"   Strengths: {', '.join(feedback['strengths'][:2])}...")
                        print(f"   Recommendations: {len(feedback['recommendations'])} provided")
                    
                    except Exception as e:
                        print(f"❌ Feedback generation failed: {str(e)}")
                else:
                    print("   Session continuing with next question...")
                    if response_result['data']['next_question']:
                        print(f"   Next question: {response_result['data']['next_question']['question']}")
                
            except Exception as e:
                print(f"❌ Response submission failed: {str(e)}")
        else:
            print("   No session ID available for response testing")
    
    except Exception as e:
        print(f"❌ Mock interview start failed: {str(e)}")
    
    # Test 5: Get recommendations
    print("\n5. Testing recommendations...")
    user_profile = {
        "user_id": "test_user_123",
        "career_goals": {
            "target_roles": ["Software Engineer", "Senior Developer"]
        },
        "skills": [
            {"name": "Python", "proficiency": 4},
            {"name": "JavaScript", "proficiency": 3},
            {"name": "System Design", "proficiency": 2}
        ],
        "recent_applications": [
            {"company": "Google", "role": "Software Engineer"},
            {"company": "Amazon", "role": "Senior Developer"}
        ]
    }
    
    try:
        recommendations = await agent.get_recommendations(user_profile)
        print(f"✅ Recommendations generated successfully!")
        print(f"   Generated {len(recommendations)} recommendations")
        
        for i, rec in enumerate(recommendations[:2]):  # Show first 2
            print(f"   {i+1}. {rec['title']} ({rec['priority']} priority)")
    
    except Exception as e:
        print(f"❌ Recommendations failed: {str(e)}")
    
    print("\n🎉 Interview Preparation Agent testing completed!")

if __name__ == "__main__":
    asyncio.run(test_interview_preparation_agent())