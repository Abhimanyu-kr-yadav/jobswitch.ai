"""
Test script for email outreach and campaign functionality
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.agents.networking import NetworkingAgent
    from app.services.email_generator import EmailTemplateGenerator
    from app.services.email_sender import EmailSender, EmailCampaignManager
    from app.integrations.watsonx import WatsonXClient
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from app.agents.networking import NetworkingAgent
    from app.services.email_generator import EmailTemplateGenerator
    from app.services.email_sender import EmailSender, EmailCampaignManager
    from app.integrations.watsonx import WatsonXClient


async def test_email_template_generation():
    """Test email template generation"""
    print("Testing Email Template Generation...")
    
    # Mock user profile
    user_profile = {
        'first_name': 'John',
        'last_name': 'Doe',
        'current_title': 'Software Engineer',
        'current_company': 'TechCorp',
        'industry': 'Technology',
        'email': 'john.doe@example.com',
        'experience_years': 5
    }
    
    # Mock contact
    contact = {
        'contact_id': 'contact_123',
        'full_name': 'Jane Smith',
        'first_name': 'Jane',
        'current_title': 'Senior Software Engineer',
        'current_company': 'Google',
        'department': 'Engineering',
        'email': 'jane.smith@google.com',
        'seniority_level': 'senior'
    }
    
    # Mock campaign context
    campaign_context = {
        'name': 'Google Outreach',
        'target_company': 'Google',
        'target_role': 'Software Engineer',
        'objective': 'networking',
        'tone': 'professional',
        'call_to_action': 'connect'
    }
    
    # Initialize email generator (without WatsonX for testing)
    email_generator = EmailTemplateGenerator(watsonx_client=None)
    
    # Test template generation
    result = await email_generator.generate_personalized_template(
        user_profile, contact, campaign_context, 'cold_outreach'
    )
    
    print(f"Template generation success: {result['success']}")
    if result['success']:
        template = result['template']
        print(f"Subject: {template['subject']}")
        print(f"Body preview: {template['body'][:200]}...")
        print(f"Word count: {template['word_count']}")
        print(f"Quality score: {template.get('quality_score', 'N/A')}")
    else:
        print(f"Error: {result.get('error')}")
    
    return result['success']


async def test_email_sending():
    """Test email sending functionality"""
    print("\nTesting Email Sending...")
    
    email_sender = EmailSender()
    
    # Test email data
    test_email = {
        'to_email': 'test@example.com',
        'subject': 'Test Email from JobSwitch.ai',
        'body': 'This is a test email to verify the email sending functionality.',
        'from_email': 'noreply@jobswitch.ai',
        'from_name': 'JobSwitch.ai',
        'enable_tracking': True
    }
    
    # Note: This will fail without proper SMTP configuration
    # but we can test the structure
    try:
        result = await email_sender.send_email(**test_email)
        print(f"Email sending result: {result}")
        return result['success']
    except Exception as e:
        print(f"Email sending failed (expected without SMTP config): {str(e)}")
        return False


async def test_campaign_management():
    """Test campaign management functionality"""
    print("\nTesting Campaign Management...")
    
    campaign_manager = EmailCampaignManager()
    
    # Mock campaign data
    campaign_id = 'test_campaign_123'
    emails = [
        {
            'to_email': 'contact1@example.com',
            'subject': 'Connection Request',
            'body': 'Hi there, I would like to connect...',
            'from_email': 'user@example.com',
            'from_name': 'Test User',
            'interaction_id': 'interaction_1',
            'contact_id': 'contact_1',
            'enable_tracking': True
        },
        {
            'to_email': 'contact2@example.com',
            'subject': 'Connection Request',
            'body': 'Hi there, I would like to connect...',
            'from_email': 'user@example.com',
            'from_name': 'Test User',
            'interaction_id': 'interaction_2',
            'contact_id': 'contact_2',
            'enable_tracking': True
        }
    ]
    
    schedule_config = {
        'daily_limit': 5,
        'start_time': '09:00',
        'end_time': '17:00',
        'timezone': 'UTC'
    }
    
    # Test campaign creation
    result = await campaign_manager.start_campaign(
        campaign_id=campaign_id,
        emails=emails,
        schedule_config=schedule_config
    )
    
    print(f"Campaign creation result: {result}")
    
    if result['success']:
        # Test campaign status
        status_result = await campaign_manager.get_campaign_status(campaign_id)
        print(f"Campaign status: {status_result}")
        
        # Test campaign pause
        pause_result = await campaign_manager.pause_campaign(campaign_id)
        print(f"Campaign pause result: {pause_result}")
        
        return True
    
    return False


async def test_networking_agent_integration():
    """Test networking agent with email functionality"""
    print("\nTesting Networking Agent Integration...")
    
    # Initialize networking agent
    networking_agent = NetworkingAgent()
    
    # Mock user input for email template generation
    user_input = {
        'action': 'generate_email_template',
        'user_id': 'user_123',
        'contact': {
            'contact_id': 'contact_456',
            'full_name': 'Alice Johnson',
            'first_name': 'Alice',
            'current_title': 'Product Manager',
            'current_company': 'Microsoft',
            'email': 'alice.johnson@microsoft.com'
        },
        'campaign_context': {
            'name': 'Microsoft Outreach',
            'target_company': 'Microsoft',
            'objective': 'job_search',
            'tone': 'professional'
        },
        'template_type': 'cold_outreach'
    }
    
    context = {
        'user_profile': {
            'first_name': 'Bob',
            'last_name': 'Wilson',
            'current_title': 'Software Developer',
            'industry': 'Technology',
            'email': 'bob.wilson@example.com'
        }
    }
    
    # Test template generation through agent
    result = await networking_agent.process_request(user_input, context)
    
    print(f"Agent template generation result: {result['success']}")
    if result['success']:
        template_data = result.get('data', {})
        template = template_data.get('template', {})
        print(f"Generated subject: {template.get('subject', 'N/A')}")
        print(f"Template body length: {len(template.get('body', ''))}")
    
    return result['success']


async def test_bulk_template_generation():
    """Test bulk template generation"""
    print("\nTesting Bulk Template Generation...")
    
    email_generator = EmailTemplateGenerator(watsonx_client=None)
    
    user_profile = {
        'first_name': 'Sarah',
        'last_name': 'Connor',
        'current_title': 'Data Scientist',
        'industry': 'Technology'
    }
    
    contacts = [
        {
            'contact_id': 'c1',
            'full_name': 'Contact One',
            'current_company': 'Company A',
            'current_title': 'Engineer'
        },
        {
            'contact_id': 'c2',
            'full_name': 'Contact Two',
            'current_company': 'Company B',
            'current_title': 'Manager'
        },
        {
            'contact_id': 'c3',
            'full_name': 'Contact Three',
            'current_company': 'Company C',
            'current_title': 'Director'
        }
    ]
    
    campaign_context = {
        'objective': 'networking',
        'tone': 'professional'
    }
    
    # Test bulk generation
    templates = await email_generator.generate_bulk_templates(
        user_profile, contacts, campaign_context, 'cold_outreach'
    )
    
    print(f"Generated {len(templates)} templates")
    success_count = sum(1 for t in templates if t.get('success', False))
    print(f"Successful generations: {success_count}/{len(templates)}")
    
    return success_count > 0


async def main():
    """Run all tests"""
    print("Starting Email Outreach and Campaign Tests...")
    print("=" * 50)
    
    tests = [
        ("Email Template Generation", test_email_template_generation),
        ("Email Sending", test_email_sending),
        ("Campaign Management", test_campaign_management),
        ("Networking Agent Integration", test_networking_agent_integration),
        ("Bulk Template Generation", test_bulk_template_generation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
            print(f"✓ {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"✗ {test_name}: ERROR - {str(e)}")
        
        print("-" * 30)
    
    # Summary
    print("\nTest Summary:")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())