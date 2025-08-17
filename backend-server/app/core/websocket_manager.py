"""
WebSocket Manager for Real-time Updates
Handles WebSocket connections and broadcasts agent activities and notifications
"""
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time updates
    """
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Accept a new WebSocket connection
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
        """
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.connection_metadata[websocket] = {
            'user_id': user_id,
            'connected_at': datetime.utcnow(),
            'last_ping': datetime.utcnow()
        }
        
        logger.info(f"WebSocket connected for user {user_id}")
        
        # Send welcome message
        await self.send_personal_message({
            'type': 'connection_established',
            'payload': {
                'message': 'Connected to JobSwitch.ai real-time updates',
                'timestamp': datetime.utcnow().isoformat()
            }
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection
        
        Args:
            websocket: WebSocket connection to remove
        """
        if websocket in self.connection_metadata:
            user_id = self.connection_metadata[websocket]['user_id']
            
            # Remove from active connections
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                
                # Clean up empty user connection sets
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove metadata
            del self.connection_metadata[websocket]
            
            logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send a message to a specific WebSocket connection
        
        Args:
            message: Message to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")
            self.disconnect(websocket)
    
    async def send_user_message(self, message: dict, user_id: str):
        """
        Send a message to all connections for a specific user
        
        Args:
            message: Message to send
            user_id: Target user ID
        """
        if user_id in self.active_connections:
            disconnected_connections = []
            
            for websocket in self.active_connections[user_id].copy():
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending user message: {str(e)}")
                    disconnected_connections.append(websocket)
            
            # Clean up disconnected connections
            for websocket in disconnected_connections:
                self.disconnect(websocket)
    
    async def broadcast_message(self, message: dict):
        """
        Broadcast a message to all connected users
        
        Args:
            message: Message to broadcast
        """
        disconnected_connections = []
        
        for user_id, connections in self.active_connections.items():
            for websocket in connections.copy():
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting message: {str(e)}")
                    disconnected_connections.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected_connections:
            self.disconnect(websocket)
    
    async def send_notification(self, user_id: str, notification: dict):
        """
        Send a notification to a specific user
        
        Args:
            user_id: Target user ID
            notification: Notification data
        """
        message = {
            'type': 'notification',
            'payload': {
                'id': notification.get('id', f"notif_{datetime.utcnow().timestamp()}"),
                'title': notification.get('title', 'New Notification'),
                'message': notification.get('message', ''),
                'type': notification.get('notification_type', 'info'),
                'agent': notification.get('agent', 'system'),
                'priority': notification.get('priority', 'medium'),
                'timestamp': datetime.utcnow().isoformat(),
                'data': notification.get('data', {})
            }
        }
        
        await self.send_user_message(message, user_id)
        logger.info(f"Notification sent to user {user_id}: {notification.get('title')}")
    
    async def send_agent_activity(self, user_id: str, activity: dict):
        """
        Send agent activity update to a specific user
        
        Args:
            user_id: Target user ID
            activity: Activity data
        """
        message = {
            'type': 'agent_activity',
            'payload': {
                'agent': activity.get('agent', 'unknown'),
                'status': activity.get('status', 'idle'),
                'message': activity.get('message', ''),
                'timestamp': datetime.utcnow().isoformat(),
                'data': activity.get('data', {})
            }
        }
        
        await self.send_user_message(message, user_id)
        logger.debug(f"Agent activity sent to user {user_id}: {activity.get('agent')} - {activity.get('status')}")
    
    async def send_recommendation_update(self, user_id: str, recommendation: dict):
        """
        Send recommendation update to a specific user
        
        Args:
            user_id: Target user ID
            recommendation: Recommendation data
        """
        message = {
            'type': 'recommendation_update',
            'payload': {
                'agent': recommendation.get('agent', 'unknown'),
                'type': recommendation.get('type', 'general'),
                'title': recommendation.get('title', 'New Recommendation'),
                'message': recommendation.get('message', ''),
                'timestamp': datetime.utcnow().isoformat(),
                'data': recommendation.get('data', {})
            }
        }
        
        await self.send_user_message(message, user_id)
        logger.info(f"Recommendation update sent to user {user_id}: {recommendation.get('title')}")
    
    async def handle_ping(self, websocket: WebSocket):
        """
        Handle ping message to keep connection alive
        
        Args:
            websocket: WebSocket connection
        """
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]['last_ping'] = datetime.utcnow()
            
            await self.send_personal_message({
                'type': 'pong',
                'payload': {
                    'timestamp': datetime.utcnow().isoformat()
                }
            }, websocket)
    
    def get_connection_stats(self) -> dict:
        """
        Get WebSocket connection statistics
        
        Returns:
            Connection statistics
        """
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        
        return {
            'total_connections': total_connections,
            'connected_users': len(self.active_connections),
            'users': list(self.active_connections.keys())
        }
    
    async def cleanup_stale_connections(self):
        """
        Clean up stale connections that haven't pinged recently
        """
        stale_threshold = datetime.utcnow().timestamp() - 300  # 5 minutes
        stale_connections = []
        
        for websocket, metadata in self.connection_metadata.items():
            if metadata['last_ping'].timestamp() < stale_threshold:
                stale_connections.append(websocket)
        
        for websocket in stale_connections:
            logger.info("Cleaning up stale WebSocket connection")
            self.disconnect(websocket)
            try:
                await websocket.close()
            except:
                pass


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


async def start_cleanup_task():
    """
    Start background task to clean up stale connections
    """
    while True:
        try:
            await websocket_manager.cleanup_stale_connections()
            await asyncio.sleep(60)  # Run every minute
        except Exception as e:
            logger.error(f"Error in WebSocket cleanup task: {str(e)}")
            await asyncio.sleep(60)