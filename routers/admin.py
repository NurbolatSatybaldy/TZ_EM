from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User, Role, BusinessElement, AccessRoleRule
from schemas import (
    RoleCreate, RoleUpdate, RoleResponse,
    BusinessElementCreate, BusinessElementUpdate, BusinessElementResponse,
    AccessRuleCreate, AccessRuleUpdate, AccessRuleResponse,
    UserResponse
)
from dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["Admin - Permission Management"])


# ==================== Role Management ====================

@router.get("/roles", response_model=List[RoleResponse])
def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get all roles
    
    Requires admin privileges
    """
    roles = db.query(Role).all()
    return roles


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new role
    
    Requires admin privileges
    """
    # Check if role already exists
    existing_role = db.query(Role).filter(Role.name == role_data.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists"
        )
    
    new_role = Role(
        name=role_data.name,
        description=role_data.description
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    
    return new_role


@router.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    role_update: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update a role
    
    Requires admin privileges
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    if role_update.name:
        # Check if new name is already taken
        existing_role = db.query(Role).filter(
            Role.name == role_update.name,
            Role.id != role_id
        ).first()
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role with this name already exists"
            )
        role.name = role_update.name
    
    if role_update.description is not None:
        role.description = role_update.description
    
    db.commit()
    db.refresh(role)
    
    return role


@router.delete("/roles/{role_id}", status_code=status.HTTP_200_OK)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete a role
    
    Requires admin privileges
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if role is in use
    users_with_role = db.query(User).filter(User.role_id == role_id).count()
    if users_with_role > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role. {users_with_role} user(s) have this role."
        )
    
    db.delete(role)
    db.commit()
    
    return {"message": "Role deleted successfully"}


# ==================== Business Element Management ====================

@router.get("/elements", response_model=List[BusinessElementResponse])
def get_business_elements(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get all business elements (resources)
    
    Requires admin privileges
    """
    elements = db.query(BusinessElement).all()
    return elements


@router.post("/elements", response_model=BusinessElementResponse, status_code=status.HTTP_201_CREATED)
def create_business_element(
    element_data: BusinessElementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new business element (resource)
    
    Requires admin privileges
    """
    # Check if element already exists
    existing_element = db.query(BusinessElement).filter(
        BusinessElement.name == element_data.name
    ).first()
    if existing_element:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business element with this name already exists"
        )
    
    new_element = BusinessElement(
        name=element_data.name,
        description=element_data.description
    )
    db.add(new_element)
    db.commit()
    db.refresh(new_element)
    
    return new_element


@router.put("/elements/{element_id}", response_model=BusinessElementResponse)
def update_business_element(
    element_id: int,
    element_update: BusinessElementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update a business element
    
    Requires admin privileges
    """
    element = db.query(BusinessElement).filter(BusinessElement.id == element_id).first()
    if not element:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business element not found"
        )
    
    if element_update.name:
        # Check if new name is already taken
        existing_element = db.query(BusinessElement).filter(
            BusinessElement.name == element_update.name,
            BusinessElement.id != element_id
        ).first()
        if existing_element:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business element with this name already exists"
            )
        element.name = element_update.name
    
    if element_update.description is not None:
        element.description = element_update.description
    
    db.commit()
    db.refresh(element)
    
    return element


@router.delete("/elements/{element_id}", status_code=status.HTTP_200_OK)
def delete_business_element(
    element_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete a business element
    
    Requires admin privileges
    """
    element = db.query(BusinessElement).filter(BusinessElement.id == element_id).first()
    if not element:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business element not found"
        )
    
    db.delete(element)
    db.commit()
    
    return {"message": "Business element deleted successfully"}


# ==================== Access Rules Management ====================

@router.get("/access-rules", response_model=List[AccessRuleResponse])
def get_access_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    role_id: int = None,
    element_id: int = None
):
    """
    Get all access rules with optional filtering
    
    - **role_id**: Filter by role (optional)
    - **element_id**: Filter by business element (optional)
    
    Requires admin privileges
    """
    query = db.query(AccessRoleRule)
    
    if role_id:
        query = query.filter(AccessRoleRule.role_id == role_id)
    if element_id:
        query = query.filter(AccessRoleRule.element_id == element_id)
    
    rules = query.all()
    return rules


@router.post("/access-rules", response_model=AccessRuleResponse, status_code=status.HTTP_201_CREATED)
def create_access_rule(
    rule_data: AccessRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new access rule
    
    Requires admin privileges
    """
    # Check if role exists
    role = db.query(Role).filter(Role.id == rule_data.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if element exists
    element = db.query(BusinessElement).filter(BusinessElement.id == rule_data.element_id).first()
    if not element:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business element not found"
        )
    
    # Check if rule already exists
    existing_rule = db.query(AccessRoleRule).filter(
        AccessRoleRule.role_id == rule_data.role_id,
        AccessRoleRule.element_id == rule_data.element_id
    ).first()
    if existing_rule:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access rule for this role and element already exists. Use update instead."
        )
    
    new_rule = AccessRoleRule(**rule_data.model_dump())
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    
    return new_rule


@router.put("/access-rules/{rule_id}", response_model=AccessRuleResponse)
def update_access_rule(
    rule_id: int,
    rule_update: AccessRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update an access rule
    
    Requires admin privileges
    """
    rule = db.query(AccessRoleRule).filter(AccessRoleRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access rule not found"
        )
    
    # Update permissions
    update_data = rule_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    
    db.commit()
    db.refresh(rule)
    
    return rule


@router.delete("/access-rules/{rule_id}", status_code=status.HTTP_200_OK)
def delete_access_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete an access rule
    
    Requires admin privileges
    """
    rule = db.query(AccessRoleRule).filter(AccessRoleRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access rule not found"
        )
    
    db.delete(rule)
    db.commit()
    
    return {"message": "Access rule deleted successfully"}


# ==================== User Management (Admin) ====================

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    include_inactive: bool = False
):
    """
    Get all users
    
    - **include_inactive**: Include inactive users (default: False)
    
    Requires admin privileges
    """
    query = db.query(User)
    
    if not include_inactive:
        query = query.filter(User.is_active == True)
    
    users = query.all()
    return users


@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update user role
    
    Requires admin privileges
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    user.role_id = role_id
    db.commit()
    db.refresh(user)
    
    return user

