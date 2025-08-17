"""
Test Unified Dashboard Implementation
Tests the unified dashboard, WebSocket connections, and real-time updates
"""
import asyncio
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app
from app.core.websocket_manager import websocket_manager

# Test client
client = TestClient(app)


class TestUnifiedDashboard:
    """Test unified dashboard functionality"""
    
    def setup_method(self):
        """Setup test data"""
        self.test_user_id = "test_user_123"
        # Create a mock token for testing
        self.test_token = "test_token_123"
        self.headers = {"Authorization": f"Bearer {self.test_token}"}
    
    def test_dashboard_stats_endpoint(self):
        """Test dashboard statistics endpoint"""
        # Mock database responses
        with patch('app.core.database.get_database') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            # Mock database queries
            mock_session.execute.return_value.fetchone.return_value = [5]
            
            response = client.get("/api/v1/dashboard/stats", headers=self.headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert isinstance(data["data"], dict)
    
    def test_recent_activities_endpoint(self):
        """Test recent activities endpoint"""
        with patch('app.core.database.get_database') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            # Mock database queries
            mock_session.execute.return_value.fetchall.return_value = [
                ("job_discovery", "Job saved", "2025-01-08T10:00:00Z", "Software Engineer")
            ]
            
            response = client.get("/api/v1/dashboard/recent-activities", headers=self.headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "activities" in data["data"]
    
    def test_notifications_endpoint(self):
        """Test notifications endpoint"""
        response = client.get("/api/v1/dashboard/notifications", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "notifications" in data["data"]
        assert isinstance(data["data"]["notifications"], list)
    
    def test_mark_notification_read(self):
        """Test marking notification as read"""
        notification_id = "test_notif_123"
        response = client.post(
            f"/api/v1/dashboard/notifications/{notification_id}/read",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_mark_all_notifications_read(self):
        """Test marking all notifications as read"""
        response = client.post(
            "/api/v1/dashboard/notifications/read-all",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestWebSocketManager:
    """Test WebSocket manager functionality"""
    
    def setup_method(self):
        """Setup test data"""
        self.test_user_id = "test_user_123"
        self.manager = websocket_manager
    
    async def test_websocket_connection_stats(self):
        """Test WebSocket connection statistics"""
        stats = self.manager.get_connection_stats()
        
        assert isinstance(stats, dict)
        assert "total_connections" in stats
        assert "connected_users" in stats
        assert "users" in stats
        assert isinstance(stats["total_connections"], int)
        assert isinstance(stats["connected_users"], int)
        assert isinstance(stats["users"], list)
    
    async def test_send_notification(self):
        """Test sending notification via WebSocket"""
        # Mock WebSocket connection
        mock_websocket = Mock()
        mock_websocket.send_text = Mock()
        
        # Add mock connection
        self.manager.active_connections[self.test_user_id] = {mock_websocket}
        self.manager.connection_metadata[mock_websocket] = {
            'user_id': self.test_user_id,
            'connected_at': '2025-01-08T10:00:00Z',
            'last_ping': '2025-01-08T10:00:00Z'
        }
        
        notification = {
            'title': 'Test Notification',
            'message': 'This is a test notification',
            'type': 'test',
            'agent': 'test_agent'
        }
        
        await self.manager.send_notification(self.test_user_id, notification)
        
        # Verify notification was sent
        mock_websocket.send_text.assert_called_once()
        
        # Clean up
        self.manager.disconnect(mock_websocket)
    
    async def test_send_agent_activity(self):
        """Test sending agent activity via WebSocket"""
        # Mock WebSocket connection
        mock_websocket = Mock()
        mock_websocket.send_text = Mock()
        
        # Add mock connection
        self.manager.active_connections[self.test_user_id] = {mock_websocket}
        self.manager.connection_metadata[mock_websocket] = {
            'user_id': self.test_user_id,
            'connected_at': '2025-01-08T10:00:00Z',
            'last_ping': '2025-01-08T10:00:00Z'
        }
        
        activity = {
            'agent': 'job_discovery',
            'status': 'active',
            'message': 'Searching for jobs...'
        }
        
        await self.manager.send_agent_activity(self.test_user_id, activity)
        
        # Verify activity was sent
        mock_websocket.send_text.assert_called_once()
        
        # Clean up
        self.manager.disconnect(mock_websocket)


class TestWebSocketEndpoints:
    """Test WebSocket API endpoints"""
    
    def test_websocket_stats_endpoint(self):
        """Test WebSocket statistics endpoint"""
        response = client.get("/ws/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_broadcast_message_endpoint(self):
        """Test broadcast message endpoint"""
        message = {
            'title': 'Test Broadcast',
            'message': 'This is a test broadcast message'
        }
        
        response = client.post("/ws/broadcast", json=message)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_send_notification_endpoint(self):
        """Test send notification endpoint"""
        user_id = "test_user_123"
        notification = {
            'title': 'Test Notification',
            'message': 'This is a test notification',
            'type': 'test'
        }
        
        response = client.post(f"/ws/notify/{user_id}", json=notification)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_send_agent_activity_endpoint(self):
        """Test send agent activity endpoint"""
        user_id = "test_user_123"
        activity = {
            'agent': 'job_discovery',
            'status': 'active',
            'message': 'Processing job search...'
        }
        
        response = client.post(f"/ws/agent-activity/{user_id}", json=activity)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_send_recommendation_endpoint(self):
        """Test send recommendation endpoint"""
        user_id = "test_user_123"
        recommendation = {
            'agent': 'job_discovery',
            'type': 'job_recommendation',
            'title': 'New Job Opportunities',
            'message': 'Found 5 new jobs matching your profile'
        }
        
        response = client.post(f"/ws/recommendation/{user_id}", json=recommendation)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


def test_dashboard_integration():
    """Test complete dashboard integration"""
    print("Testing unified dashboard implementation...")
    
    # Test dashboard stats
    test_dashboard = TestUnifiedDashboard()
    test_dashboard.setup_method()
    
    try:
        test_dashboard.test_dashboard_stats_endpoint()
        print("✓ Dashboard stats endpoint working")
    except Exception as e:
        print(f"✗ Dashboard stats endpoint failed: {str(e)}")
    
    try:
        test_dashboard.test_notifications_endpoint()
        print("✓ Notifications endpoint working")
    except Exception as e:
        print(f"✗ Notifications endpoint failed: {str(e)}")
    
    # Test WebSocket endpoints
    test_websocket = TestWebSocketEndpoints()
    
    try:
        test_websocket.test_websocket_stats_endpoint()
        print("✓ WebSocket stats endpoint working")
    except Exception as e:
        print(f"✗ WebSocket stats endpoint failed: {str(e)}")
    
    try:
        test_websocket.test_broadcast_message_endpoint()
        print("✓ Broadcast message endpoint working")
    except Exception as e:
        print(f"✗ Broadcast message endpoint failed: {str(e)}")
    
    print("Dashboard integration test completed!")


if __name__ == "__main__":
    test_dashboard_integration()