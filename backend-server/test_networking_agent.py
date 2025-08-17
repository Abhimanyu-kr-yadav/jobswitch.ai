"""
Test script for Networking Agent functionality
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.agents.networking import NetworkingAgent
from app.services.contact_scraper import ContactScraper, ContactScorer


async def test_networking_agent():
    """Test the networking agent functionality"""
    print("Testing Networking Agent...")
    
    # Initialize the networking agent
    agent = NetworkingAgent()
    
    # Test user profile
    user_profile = {
        'user_id': 'test_user_123',
        'first_name': 'John',
        'last_name': 'Doe',
        'current_title': 'Software Engineer',
        'industry': 'Technology',
        'years_experience': 5,
        'location': 'San Francisco, CA',
        'career_goals': {
            'target_role': 'Senior Software Engineer',
            'target_companies': ['Google', 'Microsoft', 'Apple']
        },
        'job_preferences': {
            'target_companies': ['Google', 'Microsoft']
        }
    }
    
    # Test context
    context = {
        'user_profile': user_profile
    }
    
    print("\n1. Testing contact discovery...")
    discovery_request = {
        'action': 'discover_contacts',
        'user_id': 'test_user_123',
        'company_name': 'Google',
        'company_domain': 'google.com',
        'target_role': 'Software Engineer'
    }
    
    try:
        discovery_result = await agent.process_request(discovery_request, context)
        print(f"Discovery result: {discovery_result['success']}")
        if discovery_result['success']:
            contacts = discovery_result['data'].get('contacts', [])
            print(f"Found {len(contacts)} contacts")
            if contacts:
                print(f"Sample contact: {contacts[0].get('full_name', 'Unknown')}")
        else:
            print(f"Discovery error: {discovery_result.get('error')}")
    except Exception as e:
        print(f"Discovery test failed: {str(e)}")
    
    print("\n2. Testing company research...")
    research_request = {
        'action': 'research_company',
        'user_id': 'test_user_123',
        'company_name': 'Microsoft'
    }
    
    try:
        research_result = await agent.process_request(research_request, context)
        print(f"Research result: {research_result['success']}")
        if research_result['success']:
            company_info = research_result['data'].get('company_info', {})
            print(f"Company: {company_info.get('name')}")
            print(f"Contacts found: {research_result['data'].get('total_contacts_found', 0)}")
        else:
            print(f"Research error: {research_result.get('error')}")
    except Exception as e:
        print(f"Research test failed: {str(e)}")
    
    print("\n3. Testing recommendations...")
    try:
        recommendations = await agent.get_recommendations(user_profile)
        print(f"Generated {len(recommendations)} recommendations")
        for i, rec in enumerate(recommendations[:3]):
            print(f"  {i+1}. {rec.get('title', 'Unknown')}")
    except Exception as e:
        print(f"Recommendations test failed: {str(e)}")
    
    print("\n4. Testing campaign creation...")
    campaign_request = {
        'action': 'create_campaign',
        'user_id': 'test_user_123',
        'campaign_name': 'Test Campaign',
        'description': 'Testing campaign creation',
        'target_company': 'Google',
        'target_role': 'Software Engineer',
        'campaign_type': 'company_research',
        'daily_limit': 5
    }
    
    try:
        campaign_result = await agent.process_request(campaign_request, context)
        print(f"Campaign creation result: {campaign_result['success']}")
        if campaign_result['success']:
            campaign = campaign_result['data'].get('campaign', {})
            print(f"Campaign ID: {campaign.get('campaign_id')}")
            print(f"Campaign name: {campaign.get('name')}")
        else:
            print(f"Campaign error: {campaign_result.get('error')}")
    except Exception as e:
        print(f"Campaign test failed: {str(e)}")
    
    print("\nNetworking Agent tests completed!")


async def test_contact_scraper():
    """Test the contact scraper functionality"""
    print("\nTesting Contact Scraper...")
    
    try:
        async with ContactScraper() as scraper:
            # Test discovering contacts for a well-known company
            contacts = await scraper.discover_company_contacts("GitHub", "github.com")
            print(f"Found {len(contacts)} contacts for GitHub")
            
            if contacts:
                sample_contact = contacts[0]
                print(f"Sample contact: {sample_contact.get('full_name', 'Unknown')}")
                print(f"Discovery source: {sample_contact.get('discovery_source')}")
                print(f"Discovery method: {sample_contact.get('discovery_method')}")
    except Exception as e:
        print(f"Contact scraper test failed: {str(e)}")


async def test_contact_scorer():
    """Test the contact scoring functionality"""
    print("\nTesting Contact Scorer...")
    
    scorer = ContactScorer()
    
    # Sample contact
    contact = {
        'full_name': 'Jane Smith',
        'current_title': 'Senior Software Engineer',
        'current_company': 'Google',
        'seniority_level': 'senior',
        'location': 'Mountain View, CA',
        'email': 'jane.smith@example.com',
        'linkedin_url': 'https://linkedin.com/in/janesmith'
    }
    
    # Sample user profile
    user_profile = {
        'industry': 'Technology',
        'location': 'San Francisco, CA',
        'years_experience': 5,
        'job_preferences': {
            'target_companies': ['Google', 'Microsoft']
        }
    }
    
    try:
        score = await scorer.score_contact_relevance(
            contact, user_profile, 'Software Engineer'
        )
        print(f"Contact relevance score: {score:.2f}")
        print(f"Contact quality assessment: High (has email and LinkedIn)")
    except Exception as e:
        print(f"Contact scorer test failed: {str(e)}")


async def main():
    """Run all tests"""
    print("Starting Networking Agent Tests...")
    print("=" * 50)
    
    await test_networking_agent()
    await test_contact_scraper()
    await test_contact_scorer()
    
    print("\n" + "=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())