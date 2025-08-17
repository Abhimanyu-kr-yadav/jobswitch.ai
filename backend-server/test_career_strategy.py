"""
Test Career Strategy Agent Implementation
"""
import asyncio
import json
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from agents.career_strategy import CareerStrategyAgent
from integrations.watsonx import WatsonXClient
from integrations.langchain_utils import LangChainAgentManager


async def test_career_strategy_agent():
    """Test the Career Strategy Agent functionality"""
    print("🚀 Testing Career Strategy Agent Implementation")
    print("=" * 60)
    
    # Initialize the agent with mock clients
    try:
        watsonx_client = WatsonXClient("test_api_key")
    except:
        # Create a mock client if initialization fails
        class MockWatsonXClient:
            async def generate_text(self, prompt):
                return {
                    "success": True,
                    "generated_text": '{"test": "mock response"}'
                }
        watsonx_client = MockWatsonXClient()
    
    try:
        langchain_manager = LangChainAgentManager()
    except:
        langchain_manager = None
    
    agent = CareerStrategyAgent(watsonx_client, langchain_manager)
    
    print(f"✅ Agent initialized: {agent.agent_id}")
    
    # Test 1: Generate Career Roadmap
    print("\n📋 Test 1: Generate Career Roadmap")
    print("-" * 40)
    
    roadmap_request = {
        "task_type": "generate_roadmap",
        "user_id": "test_user_123",
        "current_role": "Software Developer",
        "target_role": "Senior Software Engineer",
        "target_industry": "Technology",
        "timeline_months": 24,
        "target_company": "Google"
    }
    
    try:
        result = await agent.process_request(roadmap_request, {})
        print(f"✅ Roadmap generation: {'SUCCESS' if result['success'] else 'FAILED'}")
        
        if result['success']:
            roadmap_data = result['data']
            print(f"   - Roadmap ID: {roadmap_data.get('roadmap', {}).get('roadmap_id', 'N/A')}")
            print(f"   - Milestones: {len(roadmap_data.get('milestones', []))}")
            print(f"   - Goals: {len(roadmap_data.get('goals', []))}")
            print(f"   - Recommendations: {len(result.get('recommendations', []))}")
        else:
            print(f"   - Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Roadmap generation failed: {str(e)}")
    
    # Test 2: Create Career Goals
    print("\n🎯 Test 2: Create Career Goals")
    print("-" * 40)
    
    goals_request = {
        "task_type": "create_goals",
        "user_id": "test_user_123",
        "roadmap_id": "test_roadmap_123",
        "categories": ["skill_development", "experience", "networking"],
        "timeline_months": 12
    }
    
    try:
        result = await agent.process_request(goals_request, {})
        print(f"✅ Goals creation: {'SUCCESS' if result['success'] else 'FAILED'}")
        
        if result['success']:
            goals_data = result['data']
            print(f"   - Goals created: {len(goals_data.get('goals', []))}")
            print(f"   - Recommendations: {len(result.get('recommendations', []))}")
            
            # Show first goal details
            if goals_data.get('goals'):
                first_goal = goals_data['goals'][0]
                print(f"   - Sample goal: {first_goal.get('title', 'N/A')}")
                print(f"   - Category: {first_goal.get('category', 'N/A')}")
        else:
            print(f"   - Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Goals creation failed: {str(e)}")
    
    # Test 3: Track Progress
    print("\n📊 Test 3: Track Progress")
    print("-" * 40)
    
    progress_request = {
        "task_type": "track_progress",
        "user_id": "test_user_123",
        "roadmap_id": "test_roadmap_123",
        "goal_id": "test_goal_123",
        "progress_data": {
            "progress_percentage": 45,
            "notes": "Completed Kubernetes basics course and deployed first application",
            "achievements": ["Course completion", "First deployment"],
            "challenges": ["Complex networking concepts", "Performance optimization"],
            "period_start": "2024-01-01",
            "period_end": "2024-01-31"
        }
    }
    
    try:
        result = await agent.process_request(progress_request, {})
        print(f"✅ Progress tracking: {'SUCCESS' if result['success'] else 'FAILED'}")
        
        if result['success']:
            progress_data = result['data']
            print(f"   - Tracking ID: {progress_data.get('progress_record', {}).get('tracking_id', 'N/A')}")
            print(f"   - Analysis available: {'YES' if progress_data.get('analysis') else 'NO'}")
            print(f"   - Recommendations: {len(result.get('recommendations', []))}")
        else:
            print(f"   - Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Progress tracking failed: {str(e)}")
    
    # Test 4: Analyze Market Trends
    print("\n📈 Test 4: Analyze Market Trends")
    print("-" * 40)
    
    trends_request = {
        "task_type": "analyze_market_trends",
        "industry": "Technology",
        "target_role": "Senior Software Engineer",
        "location": "United States"
    }
    
    try:
        result = await agent.process_request(trends_request, {})
        print(f"✅ Market trends analysis: {'SUCCESS' if result['success'] else 'FAILED'}")
        
        if result['success']:
            trends_data = result['data']
            market_analysis = trends_data.get('market_analysis', {})
            print(f"   - Industry health: {market_analysis.get('industry_health', 'N/A')}")
            print(f"   - Role demand: {market_analysis.get('role_demand', 'N/A')}")
            print(f"   - Trending skills: {len(trends_data.get('trending_skills', []))}")
            print(f"   - Career recommendations: {len(trends_data.get('career_recommendations', []))}")
        else:
            print(f"   - Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Market trends analysis failed: {str(e)}")
    
    # Test 5: Get Career Recommendations
    print("\n💡 Test 5: Get Career Recommendations")
    print("-" * 40)
    
    user_profile = {
        "user_id": "test_user_123",
        "current_role": "Software Developer",
        "years_experience": 5,
        "industry": "Technology",
        "skills": [
            {"name": "Python", "proficiency": "advanced"},
            {"name": "JavaScript", "proficiency": "intermediate"},
            {"name": "AWS", "proficiency": "basic"}
        ],
        "career_goals": {
            "target_role": "Senior Software Engineer",
            "timeline": "2 years"
        }
    }
    
    try:
        recommendations = await agent.get_recommendations(user_profile)
        print(f"✅ Career recommendations: {'SUCCESS' if recommendations else 'FAILED'}")
        print(f"   - Recommendations count: {len(recommendations)}")
        
        if recommendations:
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"   - Recommendation {i}: {rec.get('title', 'N/A')}")
                print(f"     Priority: {rec.get('priority', 'N/A')}")
                
    except Exception as e:
        print(f"❌ Career recommendations failed: {str(e)}")
    
    # Test 6: Agent Status
    print("\n🔍 Test 6: Agent Status")
    print("-" * 40)
    
    try:
        status = await agent.get_status()
        print(f"✅ Agent status retrieved successfully")
        print(f"   - Agent ID: {status.get('agent_id', 'N/A')}")
        print(f"   - Status: {status.get('status', 'N/A')}")
        print(f"   - Context size: {status.get('context_size', 0)}")
        
    except Exception as e:
        print(f"❌ Agent status failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 Career Strategy Agent Testing Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_career_strategy_agent())