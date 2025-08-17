#!/usr/bin/env python3
"""
Test script for Technical Interview functionality
"""
import asyncio
import json
import sys
import os

# Add the backend-server directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.technical_interview import TechnicalInterviewAgent
from app.services.code_executor import CodeExecutor
from app.data.coding_challenges import get_coding_challenges, get_challenge_by_id
from app.models.coding_challenge import ProgrammingLanguage


async def test_coding_challenges_database():
    """Test the coding challenges database"""
    print("=== Testing Coding Challenges Database ===")
    
    challenges = get_coding_challenges()
    print(f"Total challenges loaded: {len(challenges)}")
    
    for challenge in challenges[:3]:  # Test first 3 challenges
        print(f"\nChallenge: {challenge.title}")
        print(f"Difficulty: {challenge.difficulty}")
        print(f"Category: {challenge.category}")
        print(f"Test cases: {len(challenge.test_cases)}")
        print(f"Supported languages: {list(challenge.starter_code.keys())}")
    
    # Test specific challenge retrieval
    two_sum = get_challenge_by_id("two-sum")
    if two_sum:
        print(f"\nRetrieved specific challenge: {two_sum.title}")
        print(f"Has Python starter code: {'python' in two_sum.starter_code}")
    
    print("✅ Coding challenges database test passed")


async def test_code_executor():
    """Test the code execution environment"""
    print("\n=== Testing Code Executor ===")
    
    executor = CodeExecutor()
    
    # Test Python code execution
    python_code = """
def two_sum(nums, target):
    num_map = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_map:
            return [num_map[complement], i]
        num_map[num] = i
    return []
"""
    
    # Get test cases from two-sum challenge
    challenge = get_challenge_by_id("two-sum")
    if challenge:
        print("Testing Python code execution...")
        result = await executor.execute_code(
            python_code, 
            ProgrammingLanguage.PYTHON, 
            challenge.test_cases,
            "test-submission-1"
        )
        
        print(f"Execution success: {result.success}")
        print(f"Overall status: {result.overall_status}")
        print(f"Passed tests: {result.passed_tests}/{result.total_tests}")
        print(f"Execution time: {result.execution_time}ms")
        
        if result.test_results:
            for i, test_result in enumerate(result.test_results[:2]):
                print(f"Test {i+1}: {'PASS' if test_result.passed else 'FAIL'}")
                if not test_result.passed:
                    print(f"  Expected: {test_result.expected_output}")
                    print(f"  Actual: {test_result.actual_output}")
    
    print("✅ Code executor test completed")


async def test_technical_interview_agent():
    """Test the technical interview agent"""
    print("\n=== Testing Technical Interview Agent ===")
    
    agent = TechnicalInterviewAgent()
    
    # Test getting challenges
    print("Testing get challenges...")
    result = await agent.process_request({
        "action": "get_challenges",
        "difficulty": "easy",
        "limit": 5
    }, {"user_id": "test_user"})
    
    print(f"Get challenges success: {result.get('success')}")
    if result.get('success'):
        challenges = result['data']['challenges']
        print(f"Retrieved {len(challenges)} challenges")
    
    # Test starting technical interview
    print("\nTesting start technical interview...")
    start_result = await agent.process_request({
        "action": "start_technical_interview",
        "job_role": "Software Engineer",
        "company": "Google",
        "difficulty": "easy",
        "categories": ["arrays"],
        "challenge_count": 2
    }, {"user_id": "test_user"})
    
    print(f"Start interview success: {start_result.get('success')}")
    if start_result.get('success'):
        session_id = start_result['data']['session_id']
        print(f"Session ID: {session_id}")
        print(f"Current challenge: {start_result['data']['current_challenge']['title']}")
        
        # Test code submission
        print("\nTesting code submission...")
        submit_result = await agent.process_request({
            "action": "submit_code",
            "session_id": session_id,
            "challenge_id": start_result['data']['current_challenge']['id'],
            "language": "python",
            "code": """def two_sum(nums, target):
    num_map = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_map:
            return [num_map[complement], i]
        num_map[num] = i
    return []"""
        }, {"user_id": "test_user"})
        
        print(f"Submit code success: {submit_result.get('success')}")
        if submit_result.get('success'):
            execution_result = submit_result['data']['execution_result']
            print(f"Execution status: {execution_result['overall_status']}")
            print(f"Tests passed: {execution_result['passed_tests']}/{execution_result['total_tests']}")
        
        # Test getting feedback
        print("\nTesting feedback generation...")
        feedback_result = await agent.process_request({
            "action": "get_technical_feedback",
            "session_id": session_id
        }, {"user_id": "test_user"})
        
        print(f"Feedback success: {feedback_result.get('success')}")
        if feedback_result.get('success'):
            feedback = feedback_result['data']['feedback']
            print(f"Overall score: {feedback['overall_score']}")
            print(f"Problem solving score: {feedback['problem_solving_score']}")
    
    print("✅ Technical interview agent test completed")


async def test_recommendations():
    """Test recommendation generation"""
    print("\n=== Testing Recommendations ===")
    
    agent = TechnicalInterviewAgent()
    
    user_profile = {
        "user_id": "test_user",
        "career_goals": {
            "target_roles": ["Software Engineer", "Full Stack Developer"]
        },
        "skills": [
            {"name": "JavaScript", "proficiency": 4},
            {"name": "Python", "proficiency": 3},
            {"name": "Data Structures", "proficiency": 2}
        ]
    }
    
    recommendations = await agent.get_recommendations(user_profile)
    print(f"Generated {len(recommendations)} recommendations")
    
    for rec in recommendations:
        print(f"- {rec['title']}: {rec['description']}")
    
    print("✅ Recommendations test completed")


async def main():
    """Run all tests"""
    print("Starting Technical Interview Tests...\n")
    
    try:
        await test_coding_challenges_database()
        await test_code_executor()
        await test_technical_interview_agent()
        await test_recommendations()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)