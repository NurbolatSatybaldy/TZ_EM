from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database import get_db
from models import User, Session as SessionModel, AccessRoleRule
from security import decode_access_token
from schemas import TokenData

security = HTTPBearer(auto_error=False)


def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from Bearer token"""
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        return None
    
    user_id: str = payload.get("sub")
    if user_id is None:
        return None
    
    try:
        user_id_int = int(user_id)
    except ValueError:
        return None
    
    # Check if it's a session token
    token_type = payload.get("type")
    if token_type == "session":
        # Verify session exists and is valid
        session = db.query(SessionModel).filter(
            SessionModel.session_token == token,
            SessionModel.user_id == user_id_int
        ).first()
        
        if not session:
            return None
        
        # Check if session is expired
        if session.expires_at < datetime.utcnow():
            db.delete(session)
            db.commit()
            return None
    
    # Get user
    user = db.query(User).filter(User.id == user_id_int).first()
    
    if user is None or not user.is_active:
        return None
    
    return user


def get_current_user(
    user: Optional[User] = Depends(get_current_user_from_token)
) -> User:
    """Require authenticated user (401 if not found)"""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_admin(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> User:
    """Require admin role"""
    # Assuming role with name "admin" is the admin role
    if current_user.role.name.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


class PermissionChecker:
    """Check if user has specific permission for a resource"""
    
    def __init__(
        self,
        element_name: str,
        permission_type: str,  # read, read_all, create, update, update_all, delete, delete_all
        owner_id: Optional[int] = None
    ):
        self.element_name = element_name
        self.permission_type = permission_type
        self.owner_id = owner_id
    
    def __call__(
        self,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        """Check permission and return user if authorized"""
        # Get the access rule for this user's role and element
        access_rule = db.query(AccessRoleRule).join(
            AccessRoleRule.element
        ).filter(
            AccessRoleRule.role_id == current_user.role_id,
            AccessRoleRule.element.has(name=self.element_name)
        ).first()
        
        if not access_rule:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: No permissions for this resource"
            )
        
        # Check if permission is granted
        permission_field = f"{self.permission_type}_permission"
        has_permission = getattr(access_rule, permission_field, False)
        
        # For operations that distinguish between "own" and "all"
        if self.permission_type in ["read", "update", "delete"]:
            all_permission_field = f"{self.permission_type}_all_permission"
            has_all_permission = getattr(access_rule, all_permission_field, False)
            
            # If user has "all" permission, grant access
            if has_all_permission:
                return current_user
            
            # If user has basic permission, check ownership
            if has_permission:
                # If owner_id is provided, check if user is the owner
                if self.owner_id is not None:
                    if current_user.id == self.owner_id:
                        return current_user
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Access denied: You can only access your own resources"
                        )
                # If no owner_id provided, allow access (list operations)
                return current_user
        else:
            # For create permission
            if has_permission:
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Missing {self.permission_type} permission"
        )

