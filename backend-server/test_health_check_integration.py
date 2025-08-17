#!/usr/bin/env python3
"""
Integration test for enhanced health check endpoint
Tests the actual health check endpoint with real system components
"""

import requests
import json
import sys
import time
from datetime import datetime


def test_health_check_integration():
    """Test the health check endpoint with a running server"""
    
    print("Testing health check endpoint integration...")
    
    # Test with local server (assuming it's running on port 8000)
    base_url = "http://localhost:8000"
    
    try:
        # Make request to health endpoint
        response = requests.get(f"{base_url}/health", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        # Parse response
        health_data = response.json()
        
        # Pretty print the response for inspection
        print("\nHealth Check Response:")
        print(json.dumps(health_data, indent=2))
        
        # Verify structure
        required_fields = ["overall_status", "orchestrator", "agents"]
        for field in required_fields:
            if field not in health_data:
                print(f"✗ Missing required field: {field}")
                return False
        
        # Check orchestrator section
        orchestrator = health_data["orchestrator"]
        orchestrator_fields = ["is_ready", "initialization_phase", "is_running", "registered_agents_count"]
        for field in orchestrator_fields:
            if field not in orchestrator:
                print(f"✗ Missing orchestrator field: {field}")
                return False
        
        # Check agents section
        agents = health_data["agents"]
        if "summary" not in agents:
            print("✗ Missing agents summary")
            return False
        
        if "registration_details" not in agents:
            print("✗ Missing agents registration_details")
            return False
        
        # Print summary information
        print(f"\n✓ Health check integration test passed!")
        print(f"✓ Overall status: {health_data['overall_status']}")
        print(f"✓ Orchestrator ready: {orchestrator['is_ready']}")
        print(f"✓ Orchestrator phase: {orchestrator['initialization_phase']}")
        print(f"✓ Registered agents: {orchestrator['registered_agents_count']}")
        
        if orchestrator['registered_agents_count'] > 0:
            print(f"✓ Agent list: {', '.join(orchestrator['registered_agents'])}")
        
        summary = agents["summary"]
        print(f"✓ Agents configured: {summary['total_configured']}")
        print(f"✓ Agents successfully registered: {summary['successfully_registered']}")
        print(f"✓ Failed registrations: {summary['failed_registrations']}")
        
        # Check for timing information
        if "timing" in agents:
            timing = agents["timing"]
            if "total_registration_time_seconds" in timing:
                print(f"✓ Registration time: {timing['total_registration_time_seconds']:.2f} seconds")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server. Make sure the server is running on localhost:8000")
        print("  You can start the server with: python -m uvicorn app.main:app --reload")
        return False
        
    except requests.exceptions.Timeout:
        print("✗ Request timed out")
        return False
        
    except Exception as e:
        print(f"✗ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run integration test"""
    print("Running health check integration test...\n")
    
    success = test_health_check_integration()
    
    if success:
        print("\n✓ Integration test passed! Enhanced health check endpoint is working correctly.")
        return True
    else:
        print("\n✗ Integration test failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)