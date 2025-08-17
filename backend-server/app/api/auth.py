"""
Authentication API endpoints
"""
import uuid
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_database
from app.core.auth import auth_manager, get_current_user
from app.models.user import UserProfile
from app.models.auth_schemas import (
    UserRegistrationRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    PasswordChangeRequest,
    RefreshTokenRequest,
    ApiResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=ApiResponse)
async def register_user(
    user_data: UserRegistrationRequest,
    db: Session = Depends(get_database)
):
    """
    Register a new user
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Registration success response
    """
    try:
        # Check if user already exists
        existing_user = db.query(UserProfile).filter(
            UserProfile.email == user_data.email
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Generate user ID
        user_id = str(uuid.uuid4())
        
        # Hash password
        password_hash = auth_manager.hash_password(user_data.password)
        
        # Create new user
        new_user = UserProfile(
            user_id=user_id,
            email=user_data.email,
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            location=user_data.location,
            profile_completion=0.3  # Basic info completed
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"New user registered: {user_data.email}")
        
        return ApiResponse(
            success=True,
            message="User registered successfully",
            data={"user_id": user_id}
        )
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {str(e)}")
        # Include more detailed error information for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLoginRequest,
    db: Session = Depends(get_database)
):
    """
    Authenticate user and return JWT tokens
    
    Args:
        login_data: User login credentials
        db: Database session
        
    Returns:
        JWT access and refresh tokens
    """
    try:
        # Find user by email
        user = db.query(UserProfile).filter(
            UserProfile.email == login_data.email
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not auth_manager.verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Create tokens
        access_token = auth_manager.create_access_token(user.user_id, user.email)
        refresh_token = auth_manager.create_refresh_token(user.user_id)
        
        logger.info(f"User logged in: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=auth_manager.expiration_hours * 3600  # Convert to seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        # Include more detailed error information for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_database)
):
    """
    Refresh access token using refresh token
    
    Args:
        refresh_data: Refresh token data
        db: Database session
        
    Returns:
        New JWT access and refresh tokens
    """
    try:
        # Verify refresh token
        payload = auth_manager.verify_token(refresh_data.refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user from database
        user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        access_token = auth_manager.create_access_token(user.user_id, user.email)
        new_refresh_token = auth_manager.create_refresh_token(user.user_id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=auth_manager.expiration_hours * 3600
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/change-password", response_model=ApiResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Change user password
    
    Args:
        password_data: Password change data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Password change success response
    """
    try:
        # Verify current password
        if not auth_manager.verify_password(password_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_password_hash = auth_manager.hash_password(password_data.new_password)
        
        # Update password
        current_user.password_hash = new_password_hash
        db.commit()
        
        logger.info(f"Password changed for user: {current_user.email}")
        
        return ApiResponse(
            success=True,
            message="Password changed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get current user profile
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile data
    """
    return UserResponse.from_orm(current_user)


@router.post("/logout", response_model=ApiResponse)
async def logout_user(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Logout user (client should discard tokens)
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Logout success response
    """
    logger.info(f"User logged out: {current_user.email}")
    
    return ApiResponse(
        success=True,
        message="Logged out successfully"
    )