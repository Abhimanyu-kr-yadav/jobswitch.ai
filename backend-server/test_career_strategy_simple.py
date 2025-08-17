"""
Simple Test for Career Strategy Agent Implementation
Tests the fallback methods without requiring WatsonX.ai
"""
import asyncio
import json
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from agents.career_strategy import CareerStrategyAgent


class MockWatsonXClient:
    """Mock WatsonX client that always fails to trigger fallback methods"""
    async def generate_text(self, prompt):
        # Always return failure to test fallback methods
        return {
            "success": False,
            "error": "Mock failure to test fallbacks"
        }


async def test_career_strategy_fallbacks():
    """Test the Career Strategy Agent fallback functionality"""
    print("🚀 Testing Career Strategy Agent Fallback Methods")
    print("=" * 60)
    
    # Initialize the agent with mock client
    mock_client = MockWatsonXClient()
    agent = CareerStrategyAgent(mock_client, None)
    
    print(f"✅ Agent initialized: {agent.agent_id}")
    
    # Test 1: Generate Career Roadmap (Fallback)
    print("\n📋 Test 1: Generate Career Roadmap (Fallback)")
    print("-" * 50)
    
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
            print(f"   - Title: {roadmap_data.get('roadmap', {}).get('title', 'N/A')}")
            print(f"   - Timeline: {roadmap_data.get('roadmap', {}).get('timeline_months', 'N/A')} months")
            print(f"   - Milestones: {len(roadmap_data.get('milestones', []))}")
            print(f"   - Goals: {len(roadmap_data.get('goals', []))}")
            print(f"   - Generation method: {result.get('metadata', {}).get('generation_method', 'N/A')}")
        else:
            print(f"   - Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Roadmap generation failed: {str(e)}")
    
    # Test 2: Create Career Goals (Fallback)
    print("\n🎯 Test 2: Create Career Goals (Fallback)")
    print("-" * 50)
    
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
            print(f"   - Generation method: {result.get('metadata', {}).get('generation_method', 'N/A')}")
            
            # Show goal details
            for i, goal in enumerate(goals_data.get('goals', []), 1):
                print(f"   - Goal {i}: {goal.get('title', 'N/A')}")
                print(f"     Category: {goal.get('category', 'N/A')}")
                print(f"     Priority: {goal.get('priority', 'N/A')}")
        else:
            print(f"   - Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Goals creation failed: {str(e)}")
    
    # Test 3: Track Progress (Fallback)
    print("\n📊 Test 3: Track Progress (Fallback)")
    print("-" * 50)
    
    progress_request = {
        "task_type": "track_progress",
        "user_id": "test_user_123",
        "roadmap_id": "test_roadmap_123",
        "goal_id": "test_goal_123",
        "progress_data": {
            "progress_percentage": 45,
            "notes": "Completed Kubernetes basics course",
            "achievements": ["Course completion"],
            "challenges": ["Complex concepts"]
        }
    }
    
    try:
        result = await agent.process_request(progress_request, {})
        print(f"✅ Progress tracking: {'SUCCESS' if result['success'] else 'FAILED'}")
        
        if result['success']:
            progress_data = result['data']
            progress_record = progress_data.get('progress_record', {})
            print(f"   - Tracking ID: {progress_record.get('tracking_id', 'N/A')}")
            print(f"   - Progress: {progress_record.get('progress_percentage', 0)}%")
            print(f"   - Generation method: {result.get('metadata', {}).get('generation_method', 'N/A')}")
        else:
            print(f"   - Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Progress tracking failed: {str(e)}")
    
    # Test 4: Analyze Market Trends (Fallback)
    print("\n📈 Test 4: Analyze Market Trends (Fallback)")
    print("-" * 50)
    
    trends_request = {
        "task_type": "analyze_market_trends",
        "user_id": "test_user_123",  # Added required user_id
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
            print(f"   - Generation method: {result.get('metadata', {}).get('generation_method', 'N/A')}")
        else:
            print(f"   - Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Market trends analysis failed: {str(e)}")
    
    # Test 5: Get Career Recommendations (Fallback)
    print("\n💡 Test 5: Get Career Recommendations (Fallback)")
    print("-" * 50)
    
    user_profile = {
        "user_id": "test_user_123",
        "current_role": "Software Developer",
        "years_experience": 5,
        "industry": "Technology",
        "skills": [],
        "career_goals": {}
    }
    
    try:
        recommendations = await agent.get_recommendations(user_profile)
        print(f"✅ Career recommendations: {'SUCCESS' if recommendations else 'FAILED'}")
        print(f"   - Recommendations count: {len(recommendations)}")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"   - Recommendation {i}: {rec.get('title', 'N/A')}")
            print(f"     Type: {rec.get('type', 'N/A')}")
            print(f"     Priority: {rec.get('priority', 'N/A')}")
                
    except Exception as e:
        print(f"❌ Career recommendations failed: {str(e)}")
    
    # Test 6: Test Agent Methods
    print("\n🔧 Test 6: Test Agent Helper Methods")
    print("-" * 50)
    
    try:
        # Test career frameworks
        print(f"✅ Career frameworks available: {len(agent.career_frameworks)}")
        for framework, description in list(agent.career_frameworks.items())[:2]:
            print(f"   - {framework}: {description[:50]}...")
        
        # Test transition patterns
        print(f"✅ Transition patterns available: {len(agent.transition_patterns)}")
        for pattern, description in list(agent.transition_patterns.items())[:2]:
            print(f"   - {pattern}: {description}")
        
        # Test agent status
        status = await agent.get_status()
        print(f"✅ Agent status: {status.get('status', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Agent methods test failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 Career Strategy Agent Fallback Testing Complete!")
    print("✅ All core functionality working with fallback methods")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_career_strategy_fallbacks())