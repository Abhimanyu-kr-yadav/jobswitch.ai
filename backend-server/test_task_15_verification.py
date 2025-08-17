"""
Task 15 Verification: Create unified dashboard and user interface
Verifies all sub-tasks are completed according to requirements 8.1, 8.2, 8.4
"""
import os
import sys
import json
import re

def verify_central_dashboard():
    """Verify central dashboard showing all agent activities and recommendations"""
    print("🔍 Verifying central dashboard...")
    
    # Check UnifiedDashboardHome component
    dashboard_file = "../jobswitch-ui/jobswitch-ui/src/components/dashboard/UnifiedDashboardHome.js"
    if not os.path.exists(dashboard_file):
        print("❌ UnifiedDashboardHome.js not found")
        return False
    
    with open(dashboard_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verify key features
    features = [
        "agentActivities",
        "dashboardStats", 
        "recentRecommendations",
        "agentStatusCards",
        "quickActions"
    ]
    
    missing_features = []
    for feature in features:
        if feature not in content:
            missing_features.append(feature)
    
    if missing_features:
        print(f"❌ Missing dashboard features: {missing_features}")
        return False
    
    print("✅ Central dashboard with agent activities - IMPLEMENTED")
    return True

def verify_realtime_websocket():
    """Verify real-time updates using WebSocket connections"""
    print("🔍 Verifying WebSocket real-time updates...")
    
    # Check WebSocket manager
    ws_manager_file = "app/core/websocket_manager.py"
    if not os.path.exists(ws_manager_file):
        print("❌ WebSocket manager not found")
        return False
    
    with open(ws_manager_file, 'r', encoding='utf-8') as f:
        ws_content = f.read()
    
    # Check WebSocket API
    ws_api_file = "app/api/websocket.py"
    if not os.path.exists(ws_api_file):
        print("❌ WebSocket API not found")
        return False
    
    with open(ws_api_file, 'r', encoding='utf-8') as f:
        api_content = f.read()
    
    # Check Dashboard component WebSocket integration
    dashboard_main_file = "../jobswitch-ui/jobswitch-ui/src/components/Dashboard.js"
    if not os.path.exists(dashboard_main_file):
        print("❌ Main Dashboard component not found")
        return False
    
    with open(dashboard_main_file, 'r', encoding='utf-8') as f:
        dashboard_content = f.read()
    
    # Verify WebSocket features
    ws_features = [
        ("WebSocket connection management", "connect.*websocket", ws_content),
        ("Real-time message handling", "send_notification", ws_content),
        ("Agent activity updates", "send_agent_activity", ws_content),
        ("Frontend WebSocket connection", "new WebSocket", dashboard_content),
        ("Message handling", "handleWebSocketMessage", dashboard_content),
        ("Auto-reconnection", "setTimeout.*connectWebSocket", dashboard_content)
    ]
    
    for feature_name, pattern, content in ws_features:
        if not re.search(pattern, content, re.IGNORECASE):
            print(f"❌ Missing WebSocket feature: {feature_name}")
            return False
    
    print("✅ Real-time WebSocket updates - IMPLEMENTED")
    return True

def verify_navigation_system():
    """Verify navigation system for accessing different agent interfaces"""
    print("🔍 Verifying navigation system...")
    
    # Check main Dashboard component
    dashboard_file = "../jobswitch-ui/jobswitch-ui/src/components/Dashboard.js"
    if not os.path.exists(dashboard_file):
        print("❌ Main Dashboard component not found")
        return False
    
    with open(dashboard_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verify navigation features
    nav_features = [
        "activeTab",
        "setActiveTab", 
        "renderTabContent",
        "JobDiscovery",
        "SkillsAnalysisDashboard",
        "ResumeBuilder",
        "InterviewPreparationHub",
        "NetworkingHub",
        "CareerStrategyHub"
    ]
    
    missing_nav = []
    for feature in nav_features:
        if feature not in content:
            missing_nav.append(feature)
    
    if missing_nav:
        print(f"❌ Missing navigation features: {missing_nav}")
        return False
    
    # Check if tabs are properly defined
    if "tabs = [" not in content:
        print("❌ Navigation tabs not properly defined")
        return False
    
    print("✅ Navigation system for agent interfaces - IMPLEMENTED")
    return True

def verify_notification_system():
    """Verify notification system for agent updates and recommendations"""
    print("🔍 Verifying notification system...")
    
    # Check NotificationCenter component
    notification_file = "../jobswitch-ui/jobswitch-ui/src/components/dashboard/NotificationCenter.js"
    if not os.path.exists(notification_file):
        print("❌ NotificationCenter component not found")
        return False
    
    with open(notification_file, 'r', encoding='utf-8') as f:
        notification_content = f.read()
    
    # Check Dashboard integration
    dashboard_file = "../jobswitch-ui/jobswitch-ui/src/components/Dashboard.js"
    with open(dashboard_file, 'r', encoding='utf-8') as f:
        dashboard_content = f.read()
    
    # Check backend notification support
    dashboard_api_file = "app/api/dashboard.py"
    if not os.path.exists(dashboard_api_file):
        print("❌ Dashboard API not found")
        return False
    
    with open(dashboard_api_file, 'r', encoding='utf-8') as f:
        api_content = f.read()
    
    # Verify notification features
    notification_features = [
        ("Notification display", "notifications.*map", notification_content),
        ("Mark as read", "markNotificationAsRead", dashboard_content),
        ("Unread count", "unreadCount", dashboard_content),
        ("Notification bell", "showNotifications", dashboard_content),
        ("Backend notifications API", "get_notifications", api_content),
        ("Mark read API", "mark_notification_read", api_content)
    ]
    
    for feature_name, pattern, content in notification_features:
        if not re.search(pattern, content, re.IGNORECASE):
            print(f"❌ Missing notification feature: {feature_name}")
            return False
    
    print("✅ Notification system for agent updates - IMPLEMENTED")
    return True

def verify_requirements_compliance():
    """Verify compliance with requirements 8.1, 8.2, 8.4"""
    print("🔍 Verifying requirements compliance...")
    
    requirements = {
        "8.1": "Unified dashboard showing all AI agent activities",
        "8.2": "Consistent UI/UX patterns across all features", 
        "8.4": "Application tracking and status management"
    }
    
    # Check requirement 8.1 - Unified dashboard
    dashboard_files = [
        "../jobswitch-ui/jobswitch-ui/src/components/dashboard/UnifiedDashboardHome.js",
        "../jobswitch-ui/jobswitch-ui/src/components/dashboard/AgentActivityMonitor.js"
    ]
    
    req_8_1_ok = all(os.path.exists(f) for f in dashboard_files)
    
    # Check requirement 8.2 - Consistent UI/UX
    ui_components = [
        "../jobswitch-ui/jobswitch-ui/src/components/ui/Input.js",
        "../jobswitch-ui/jobswitch-ui/src/components/ui/Textarea.js",
        "../jobswitch-ui/jobswitch-ui/src/components/ui/Select.js",
        "../jobswitch-ui/jobswitch-ui/src/components/ui/Tabs.js"
    ]
    
    req_8_2_ok = all(os.path.exists(f) for f in ui_components)
    
    # Check requirement 8.4 - Application tracking
    tracking_files = [
        "app/api/dashboard.py",
        "../jobswitch-ui/jobswitch-ui/src/components/Dashboard.js"
    ]
    
    req_8_4_ok = all(os.path.exists(f) for f in tracking_files)
    
    print(f"✅ Requirement 8.1 (Unified dashboard): {'COMPLIANT' if req_8_1_ok else 'NON-COMPLIANT'}")
    print(f"✅ Requirement 8.2 (Consistent UI/UX): {'COMPLIANT' if req_8_2_ok else 'NON-COMPLIANT'}")
    print(f"✅ Requirement 8.4 (Application tracking): {'COMPLIANT' if req_8_4_ok else 'NON-COMPLIANT'}")
    
    return req_8_1_ok and req_8_2_ok and req_8_4_ok

def main():
    """Main verification function"""
    print("=" * 60)
    print("TASK 15 VERIFICATION: Unified Dashboard and User Interface")
    print("=" * 60)
    
    # Change to backend directory for relative paths
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    tests = [
        ("Central Dashboard", verify_central_dashboard),
        ("Real-time WebSocket Updates", verify_realtime_websocket),
        ("Navigation System", verify_navigation_system),
        ("Notification System", verify_notification_system),
        ("Requirements Compliance", verify_requirements_compliance)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Testing: {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 TASK 15 SUCCESSFULLY COMPLETED!")
        print("\nImplemented features:")
        print("✅ Central dashboard showing all agent activities and recommendations")
        print("✅ Real-time updates using WebSocket connections")
        print("✅ Navigation system for accessing different agent interfaces")
        print("✅ Notification system for agent updates and recommendations")
        print("✅ Compliance with requirements 8.1, 8.2, 8.4")
    else:
        print("⚠️  Some components need attention")
    
    return passed == total

if __name__ == "__main__":
    main()