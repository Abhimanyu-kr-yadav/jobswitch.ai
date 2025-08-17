"""
JWT Authentication and Security Utilities
"""
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends, WebSocket, WebSocketException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from app.core.config import settings
from app.core.database import get_database
from app.models.user import UserProfile

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer()


class AuthManager:
    """
    Authentication and authorization manager
    """
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.jwt_algorithm
        self.expiration_hours = settings.jwt_expiration_hours
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """
        Create a JWT access token
        
        Args:
            user_id: User ID
            email: User email
            
        Returns:
            JWT token string
        """
        try:
            payload = {
                "user_id": user_id,
                "email": email,
                "exp": datetime.utcnow() + timedelta(hours=self.expiration_hours),
                "iat": datetime.utcnow(),
                "type": "access"
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token
            
        except Exception as e:
            logger.error(f"Token creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create access token"
            )
    
    def create_refresh_token(self, user_id: str) -> str:
        """
        Create a JWT refresh token
        
        Args:
            user_id: User ID
            
        Returns:
            JWT refresh token string
        """
        try:
            payload = {
                "user_id": user_id,
                "exp": datetime.utcnow() + timedelta(days=30),  # Refresh tokens last 30 days
                "iat": datetime.utcnow(),
                "type": "refresh"
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token
            
        except Exception as e:
            logger.error(f"Refresh token creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create refresh token"
            )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security), 
                        db: Session = Depends(get_database)) -> UserProfile:
        """
        Get current authenticated user from JWT token
        
        Args:
            credentials: HTTP authorization credentials
            db: Database session
            
        Returns:
            Current user profile
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Verify token
            payload = self.verify_token(credentials.credentials)
            user_id = payload.get("user_id")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Get user from database
            user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive"
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )


# Global auth manager instance
auth_manager = AuthManager()

# Dependency functions for FastAPI
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                    db: Session = Depends(get_database)) -> UserProfile:
    """
    FastAPI dependency to get current authenticated user
    """
    return auth_manager.get_current_user(credentials, db)


def get_current_active_user(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """
    FastAPI dependency to get current active user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_user_websocket(websocket: WebSocket, token: str = None) -> Optional[UserProfile]:
    """
    Get current authenticated user for WebSocket connections
    
    Args:
        websocket: WebSocket connection
        token: JWT token (optional, can be passed via query params)
        
    Returns:
        Current user profile or None if authentication fails
    """
    try:
        # For demo purposes, we'll skip authentication
        # In production, you'd validate the token properly
        if token:
            payload = auth_manager.verify_token(token)
            user_id = payload.get("user_id")
            
            if user_id:
                # In a real implementation, you'd query the database
                # For now, we'll return a mock user
                return UserProfile(
                    user_id=user_id,
                    email=payload.get("email", ""),
                    is_active=True
                )
        
        return None
        
    except Exception as e:
        logger.error(f"WebSocket authentication error: {str(e)}")
        return None


def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)), 
                             db: Session = Depends(get_database)) -> Optional[UserProfile]:
    """
    Get current authenticated user (optional - returns None if not authenticated)
    Used for endpoints that work with or without authentication
    """
    if not credentials:
        return None
    
    try:
        return auth_manager.get_current_user(credentials, db)
    except Exception:
        return None