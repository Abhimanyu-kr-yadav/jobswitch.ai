"""
WebSocket API Endpoints
Real-time communication for dashboard updates
"""
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from app.core.websocket_manager import websocket_manager
from app.core.auth import get_current_user_websocket
from app.models.user import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time updates
    
    Args:
        websocket: WebSocket connection
        user_id: User identifier
    """
    try:
        # Validate user (in a real implementation, you'd validate the user_id)
        # For now, we'll accept any user_id for demo purposes
        
        await websocket_manager.connect(websocket, user_id)
        
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                message_type = message.get('type', 'unknown')
                
                if message_type == 'ping':
                    await websocket_manager.handle_ping(websocket)
                elif message_type == 'subscribe':
                    # Handle subscription to specific agent updates
                    await handle_subscription(websocket, user_id, message.get('payload', {}))
                elif message_type == 'unsubscribe':
                    # Handle unsubscription
                    await handle_unsubscription(websocket, user_id, message.get('payload', {}))
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.error("Invalid JSON received from WebSocket client")
                await websocket_manager.send_personal_message({
                    'type': 'error',
                    'payload': {
                        'message': 'Invalid JSON format'
                    }
                }, websocket)
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {str(e)}")
                await websocket_manager.send_personal_message({
                    'type': 'error',
                    'payload': {
                        'message': 'Internal server error'
                    }
                }, websocket)
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    finally:
        websocket_manager.disconnect(websocket)


async def handle_subscription(websocket: WebSocket, user_id: str, payload: dict):
    """
    Handle subscription to specific updates
    
    Args:
        websocket: WebSocket connection
        user_id: User identifier
        payload: Subscription payload
    """
    subscription_type = payload.get('subscription_type', 'all')
    
    # Send confirmation
    await websocket_manager.send_personal_message({
        'type': 'subscription_confirmed',
        'payload': {
            'subscription_type': subscription_type,
            'message': f'Subscribed to {subscription_type} updates'
        }
    }, websocket)
    
    logger.info(f"User {user_id} subscribed to {subscription_type} updates")


async def handle_unsubscription(websocket: WebSocket, user_id: str, payload: dict):
    """
    Handle unsubscription from specific updates
    
    Args:
        websocket: WebSocket connection
        user_id: User identifier
        payload: Unsubscription payload
    """
    subscription_type = payload.get('subscription_type', 'all')
    
    # Send confirmation
    await websocket_manager.send_personal_message({
        'type': 'unsubscription_confirmed',
        'payload': {
            'subscription_type': subscription_type,
            'message': f'Unsubscribed from {subscription_type} updates'
        }
    }, websocket)
    
    logger.info(f"User {user_id} unsubscribed from {subscription_type} updates")


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics
    
    Returns:
        WebSocket connection statistics
    """
    try:
        stats = websocket_manager.get_connection_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ws/broadcast")
async def broadcast_message(message: dict):
    """
    Broadcast a message to all connected users
    (Admin endpoint - would need proper authentication in production)
    
    Args:
        message: Message to broadcast
    """
    try:
        await websocket_manager.broadcast_message({
            'type': 'broadcast',
            'payload': message
        })
        
        return {
            "success": True,
            "message": "Message broadcasted successfully"
        }
    except Exception as e:
        logger.error(f"Error broadcasting message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ws/notify/{user_id}")
async def send_notification(user_id: str, notification: dict):
    """
    Send a notification to a specific user
    (Internal endpoint for agent notifications)
    
    Args:
        user_id: Target user ID
        notification: Notification data
    """
    try:
        await websocket_manager.send_notification(user_id, notification)
        
        return {
            "success": True,
            "message": f"Notification sent to user {user_id}"
        }
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ws/agent-activity/{user_id}")
async def send_agent_activity(user_id: str, activity: dict):
    """
    Send agent activity update to a specific user
    (Internal endpoint for agent activity updates)
    
    Args:
        user_id: Target user ID
        activity: Activity data
    """
    try:
        await websocket_manager.send_agent_activity(user_id, activity)
        
        return {
            "success": True,
            "message": f"Agent activity sent to user {user_id}"
        }
    except Exception as e:
        logger.error(f"Error sending agent activity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ws/recommendation/{user_id}")
async def send_recommendation_update(user_id: str, recommendation: dict):
    """
    Send recommendation update to a specific user
    (Internal endpoint for recommendation updates)
    
    Args:
        user_id: Target user ID
        recommendation: Recommendation data
    """
    try:
        await websocket_manager.send_recommendation_update(user_id, recommendation)
        
        return {
            "success": True,
            "message": f"Recommendation update sent to user {user_id}"
        }
    except Exception as e:
        logger.error(f"Error sending recommendation update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))