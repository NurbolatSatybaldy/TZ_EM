from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User
from schemas import MockObjectResponse
from dependencies import get_current_active_user, PermissionChecker

router = APIRouter(prefix="/resources", tags=["Mock Business Resources"])

# Mock data for demonstration
MOCK_PRODUCTS = [
    {"id": 1, "name": "Product A", "owner_id": 1, "description": "First product"},
    {"id": 2, "name": "Product B", "owner_id": 2, "description": "Second product"},
    {"id": 3, "name": "Product C", "owner_id": 1, "description": "Third product"},
]

MOCK_ORDERS = [
    {"id": 1, "name": "Order #001", "owner_id": 1, "description": "Order for Product A"},
    {"id": 2, "name": "Order #002", "owner_id": 2, "description": "Order for Product B"},
    {"id": 3, "name": "Order #003", "owner_id": 3, "description": "Order for Product C"},
]

MOCK_STORES = [
    {"id": 1, "name": "Store Alpha", "owner_id": 1, "description": "Main store"},
    {"id": 2, "name": "Store Beta", "owner_id": 2, "description": "Secondary store"},
]


# ==================== Products ====================

@router.get("/products", response_model=List[MockObjectResponse])
def get_products(
    current_user: User = Depends(PermissionChecker("products", "read")),
    db: Session = Depends(get_db)
):
    """
    Get all products
    
    Requires: read permission on 'products' resource
    
    - If user has read_all_permission: returns all products
    - If user has read_permission only: returns only user's own products
    """
    # Check if user has read_all permission
    from models import AccessRoleRule
    access_rule = db.query(AccessRoleRule).join(
        AccessRoleRule.element
    ).filter(
        AccessRoleRule.role_id == current_user.role_id,
        AccessRoleRule.element.has(name="products")
    ).first()
    
    if access_rule and access_rule.read_all_permission:
        return MOCK_PRODUCTS
    else:
        # Return only user's own products
        return [p for p in MOCK_PRODUCTS if p["owner_id"] == current_user.id]


@router.get("/products/{product_id}", response_model=MockObjectResponse)
def get_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific product
    
    Requires: read permission on 'products' resource
    
    - If user has read_all_permission: can view any product
    - If user has read_permission only: can only view own products
    """
    # Find product
    product = next((p for p in MOCK_PRODUCTS if p["id"] == product_id), None)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check permission with ownership
    permission_checker = PermissionChecker("products", "read", owner_id=product["owner_id"])
    permission_checker(current_user=current_user, db=db)
    
    return product


@router.post("/products", response_model=MockObjectResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    name: str,
    description: str,
    current_user: User = Depends(PermissionChecker("products", "create")),
    db: Session = Depends(get_db)
):
    """
    Create a new product
    
    Requires: create permission on 'products' resource
    """
    new_id = max([p["id"] for p in MOCK_PRODUCTS]) + 1 if MOCK_PRODUCTS else 1
    new_product = {
        "id": new_id,
        "name": name,
        "owner_id": current_user.id,
        "description": description
    }
    MOCK_PRODUCTS.append(new_product)
    
    return new_product


@router.put("/products/{product_id}", response_model=MockObjectResponse)
def update_product(
    product_id: int,
    name: str = None,
    description: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a product
    
    Requires: update permission on 'products' resource
    
    - If user has update_all_permission: can update any product
    - If user has update_permission only: can only update own products
    """
    # Find product
    product = next((p for p in MOCK_PRODUCTS if p["id"] == product_id), None)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check permission with ownership
    permission_checker = PermissionChecker("products", "update", owner_id=product["owner_id"])
    permission_checker(current_user=current_user, db=db)
    
    # Update product
    if name:
        product["name"] = name
    if description:
        product["description"] = description
    
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a product
    
    Requires: delete permission on 'products' resource
    
    - If user has delete_all_permission: can delete any product
    - If user has delete_permission only: can only delete own products
    """
    # Find product
    product = next((p for p in MOCK_PRODUCTS if p["id"] == product_id), None)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check permission with ownership
    permission_checker = PermissionChecker("products", "delete", owner_id=product["owner_id"])
    permission_checker(current_user=current_user, db=db)
    
    # Delete product
    MOCK_PRODUCTS.remove(product)
    
    return {"message": "Product deleted successfully"}


# ==================== Orders ====================

@router.get("/orders", response_model=List[MockObjectResponse])
def get_orders(
    current_user: User = Depends(PermissionChecker("orders", "read")),
    db: Session = Depends(get_db)
):
    """
    Get all orders
    
    Requires: read permission on 'orders' resource
    """
    from models import AccessRoleRule
    access_rule = db.query(AccessRoleRule).join(
        AccessRoleRule.element
    ).filter(
        AccessRoleRule.role_id == current_user.role_id,
        AccessRoleRule.element.has(name="orders")
    ).first()
    
    if access_rule and access_rule.read_all_permission:
        return MOCK_ORDERS
    else:
        return [o for o in MOCK_ORDERS if o["owner_id"] == current_user.id]


@router.get("/orders/{order_id}", response_model=MockObjectResponse)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific order
    
    Requires: read permission on 'orders' resource
    """
    order = next((o for o in MOCK_ORDERS if o["id"] == order_id), None)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    permission_checker = PermissionChecker("orders", "read", owner_id=order["owner_id"])
    permission_checker(current_user=current_user, db=db)
    
    return order


# ==================== Stores ====================

@router.get("/stores", response_model=List[MockObjectResponse])
def get_stores(
    current_user: User = Depends(PermissionChecker("stores", "read")),
    db: Session = Depends(get_db)
):
    """
    Get all stores
    
    Requires: read permission on 'stores' resource
    """
    from models import AccessRoleRule
    access_rule = db.query(AccessRoleRule).join(
        AccessRoleRule.element
    ).filter(
        AccessRoleRule.role_id == current_user.role_id,
        AccessRoleRule.element.has(name="stores")
    ).first()
    
    if access_rule and access_rule.read_all_permission:
        return MOCK_STORES
    else:
        return [s for s in MOCK_STORES if s["owner_id"] == current_user.id]


@router.get("/stores/{store_id}", response_model=MockObjectResponse)
def get_store(
    store_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific store
    
    Requires: read permission on 'stores' resource
    """
    store = next((s for s in MOCK_STORES if s["id"] == store_id), None)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    permission_checker = PermissionChecker("stores", "read", owner_id=store["owner_id"])
    permission_checker(current_user=current_user, db=db)
    
    return store

