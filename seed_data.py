"""
Seed script to populate database with test data
Run this script after creating the database to set up initial roles, 
business elements, access rules, and test users.
"""
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User, Role, BusinessElement, AccessRoleRule
from security import get_password_hash


def seed_database():
    """Seed the database with initial data"""
    db = SessionLocal()
    
    try:
        print("Starting database seeding...")
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Check if data already exists
        if db.query(Role).first():
            print("Database already seeded. Skipping...")
            return
        
        # ==================== Create Roles ====================
        print("\n1. Creating roles...")
        
        admin_role = Role(
            name="admin",
            description="Администратор с полным доступом ко всем ресурсам"
        )
        
        manager_role = Role(
            name="manager",
            description="Менеджер с доступом к управлению товарами и заказами"
        )
        
        user_role = Role(
            name="user",
            description="Обычный пользователь с ограниченным доступом"
        )
        
        guest_role = Role(
            name="guest",
            description="Гость с минимальными правами (только чтение)"
        )
        
        db.add_all([admin_role, manager_role, user_role, guest_role])
        db.commit()
        db.refresh(admin_role)
        db.refresh(manager_role)
        db.refresh(user_role)
        db.refresh(guest_role)
        
        print(f"   ✓ Created role: {admin_role.name} (ID: {admin_role.id})")
        print(f"   ✓ Created role: {manager_role.name} (ID: {manager_role.id})")
        print(f"   ✓ Created role: {user_role.name} (ID: {user_role.id})")
        print(f"   ✓ Created role: {guest_role.name} (ID: {guest_role.id})")
        
        # ==================== Create Business Elements ====================
        print("\n2. Creating business elements (resources)...")
        
        users_element = BusinessElement(
            name="users",
            description="Управление пользователями"
        )
        
        products_element = BusinessElement(
            name="products",
            description="Управление товарами"
        )
        
        stores_element = BusinessElement(
            name="stores",
            description="Управление магазинами"
        )
        
        orders_element = BusinessElement(
            name="orders",
            description="Управление заказами"
        )
        
        permissions_element = BusinessElement(
            name="permissions",
            description="Управление правами доступа"
        )
        
        db.add_all([
            users_element,
            products_element,
            stores_element,
            orders_element,
            permissions_element
        ])
        db.commit()
        db.refresh(users_element)
        db.refresh(products_element)
        db.refresh(stores_element)
        db.refresh(orders_element)
        db.refresh(permissions_element)
        
        print(f"   ✓ Created element: {users_element.name} (ID: {users_element.id})")
        print(f"   ✓ Created element: {products_element.name} (ID: {products_element.id})")
        print(f"   ✓ Created element: {stores_element.name} (ID: {stores_element.id})")
        print(f"   ✓ Created element: {orders_element.name} (ID: {orders_element.id})")
        print(f"   ✓ Created element: {permissions_element.name} (ID: {permissions_element.id})")
        
        # ==================== Create Access Rules ====================
        print("\n3. Creating access rules...")
        
        rules = []
        
        # ADMIN - Full access to everything
        for element in [users_element, products_element, stores_element, orders_element, permissions_element]:
            rules.append(AccessRoleRule(
                role_id=admin_role.id,
                element_id=element.id,
                read_permission=True,
                read_all_permission=True,
                create_permission=True,
                update_permission=True,
                update_all_permission=True,
                delete_permission=True,
                delete_all_permission=True
            ))
        print(f"   ✓ Created {len([users_element, products_element, stores_element, orders_element, permissions_element])} rules for {admin_role.name}")
        
        # MANAGER - Can manage products, orders, and stores (all), read users
        rules.append(AccessRoleRule(
            role_id=manager_role.id,
            element_id=products_element.id,
            read_permission=True,
            read_all_permission=True,
            create_permission=True,
            update_permission=True,
            update_all_permission=True,
            delete_permission=True,
            delete_all_permission=True
        ))
        
        rules.append(AccessRoleRule(
            role_id=manager_role.id,
            element_id=orders_element.id,
            read_permission=True,
            read_all_permission=True,
            create_permission=True,
            update_permission=True,
            update_all_permission=True,
            delete_permission=True,
            delete_all_permission=True
        ))
        
        rules.append(AccessRoleRule(
            role_id=manager_role.id,
            element_id=stores_element.id,
            read_permission=True,
            read_all_permission=True,
            create_permission=True,
            update_permission=True,
            update_all_permission=True,
            delete_permission=True,
            delete_all_permission=True
        ))
        
        rules.append(AccessRoleRule(
            role_id=manager_role.id,
            element_id=users_element.id,
            read_permission=True,
            read_all_permission=True,
            create_permission=False,
            update_permission=False,
            update_all_permission=False,
            delete_permission=False,
            delete_all_permission=False
        ))
        print(f"   ✓ Created 4 rules for {manager_role.name}")
        
        # USER - Can read all products/stores, manage own orders
        rules.append(AccessRoleRule(
            role_id=user_role.id,
            element_id=products_element.id,
            read_permission=True,
            read_all_permission=True,
            create_permission=False,
            update_permission=False,
            update_all_permission=False,
            delete_permission=False,
            delete_all_permission=False
        ))
        
        rules.append(AccessRoleRule(
            role_id=user_role.id,
            element_id=stores_element.id,
            read_permission=True,
            read_all_permission=True,
            create_permission=False,
            update_permission=False,
            update_all_permission=False,
            delete_permission=False,
            delete_all_permission=False
        ))
        
        rules.append(AccessRoleRule(
            role_id=user_role.id,
            element_id=orders_element.id,
            read_permission=True,  # Can read own orders
            read_all_permission=False,
            create_permission=True,
            update_permission=True,  # Can update own orders
            update_all_permission=False,
            delete_permission=True,  # Can delete own orders
            delete_all_permission=False
        ))
        print(f"   ✓ Created 3 rules for {user_role.name}")
        
        # GUEST - Read-only access to products and stores
        rules.append(AccessRoleRule(
            role_id=guest_role.id,
            element_id=products_element.id,
            read_permission=True,
            read_all_permission=True,
            create_permission=False,
            update_permission=False,
            update_all_permission=False,
            delete_permission=False,
            delete_all_permission=False
        ))
        
        rules.append(AccessRoleRule(
            role_id=guest_role.id,
            element_id=stores_element.id,
            read_permission=True,
            read_all_permission=True,
            create_permission=False,
            update_permission=False,
            update_all_permission=False,
            delete_permission=False,
            delete_all_permission=False
        ))
        print(f"   ✓ Created 2 rules for {guest_role.name}")
        
        db.add_all(rules)
        db.commit()
        
        # ==================== Create Test Users ====================
        print("\n4. Creating test users...")
        
        admin_user = User(
            email="admin@example.com",
            first_name="Иван",
            last_name="Админов",
            middle_name="Петрович",
            hashed_password=get_password_hash("admin123"),
            role_id=admin_role.id,
            is_active=True
        )
        
        manager_user = User(
            email="manager@example.com",
            first_name="Мария",
            last_name="Менеджерова",
            middle_name="Сергеевна",
            hashed_password=get_password_hash("manager123"),
            role_id=manager_role.id,
            is_active=True
        )
        
        regular_user = User(
            email="user@example.com",
            first_name="Алексей",
            last_name="Пользователев",
            middle_name="Иванович",
            hashed_password=get_password_hash("user123"),
            role_id=user_role.id,
            is_active=True
        )
        
        guest_user = User(
            email="guest@example.com",
            first_name="Гость",
            last_name="Гостев",
            middle_name=None,
            hashed_password=get_password_hash("guest123"),
            role_id=guest_role.id,
            is_active=True
        )
        
        db.add_all([admin_user, manager_user, regular_user, guest_user])
        db.commit()
        
        print(f"   ✓ Created user: {admin_user.email} (Password: admin123)")
        print(f"   ✓ Created user: {manager_user.email} (Password: manager123)")
        print(f"   ✓ Created user: {regular_user.email} (Password: user123)")
        print(f"   ✓ Created user: {guest_user.email} (Password: guest123)")
        
        print("\n" + "="*60)
        print("✅ Database seeding completed successfully!")
        print("="*60)
        print("\n📋 Test Credentials:")
        print("   Admin:   admin@example.com / admin123")
        print("   Manager: manager@example.com / manager123")
        print("   User:    user@example.com / user123")
        print("   Guest:   guest@example.com / guest123")
        print("\n🚀 You can now start the application with: uvicorn main:app --reload")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

