from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User, Session as SessionModel
from schemas import UserResponse, UserUpdate
from dependencies import get_current_active_user

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user profile
    
    Requires authentication
    """
    return current_user


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile
    
    - **first_name**: New first name (optional)
    - **last_name**: New last name (optional)
    - **middle_name**: New middle name (optional)
    - **email**: New email (optional, must be unique)
    
    Requires authentication
    """
    # Check if email is being changed and if it's already taken
    if user_update.email and user_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
    
    # Update other fields
    if user_update.first_name:
        current_user.first_name = user_update.first_name
    if user_update.last_name:
        current_user.last_name = user_update.last_name
    if user_update.middle_name is not None:
        current_user.middle_name = user_update.middle_name
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.delete("/me", status_code=status.HTTP_200_OK)
def delete_my_account(
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete current user account
    
    Sets is_active to False, logs out user, and prevents future logins.
    Account data remains in database.
    
    Requires authentication
    """
    # Set user as inactive (soft delete)
    current_user.is_active = False
    
    # Delete all user sessions (logout)
    db.query(SessionModel).filter(SessionModel.user_id == current_user.id).delete()
    
    db.commit()
    
    # Clear cookie
    response.delete_cookie(key="session_token")
    
    return {
        "message": "Account successfully deactivated. You have been logged out."
    }

