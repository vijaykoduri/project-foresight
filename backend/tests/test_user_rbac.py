import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException, status
from app.api.deps import require_roles
from app.models.user import User, Role

def test_user_role_permissions():
    # 1. User should have role "user"
    user_role = Role(name="user")
    user = User(id=1, email="newuser@example.com", is_active=True)
    user.role = user_role
    user.jwt_role = "user"
    
    # 2. Check that "user" can access endpoints allowing core roles
    core_roles = ["admin", "manager", "user"]
    
    # Verify core workflows (adjust stock, generate forecast, scan alerts) allow "user"
    checker = require_roles(*core_roles)
    assert checker(current_user=user) == user

def test_user_cannot_manage_users_or_roles():
    # User with jwt_role "user"
    user = User(id=1, email="newuser@example.com", is_active=True)
    user.role = Role(name="user")
    user.jwt_role = "user"
    
    # User management requires "admin" role
    admin_checker = require_roles("admin")
    
    # Verify "user" is denied access
    with pytest.raises(HTTPException) as exc_info:
        admin_checker(current_user=user)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "Insufficient permissions"

def test_admin_can_perform_all_operations():
    # Admin user
    admin = User(id=2, email="admin@foresight.local", is_active=True)
    admin.role = Role(name="admin")
    admin.jwt_role = "admin"
    
    # Admin can access core endpoints
    core_checker = require_roles("admin", "manager", "user")
    assert core_checker(current_user=admin) == admin
    
    # Admin can access admin-only endpoints
    admin_checker = require_roles("admin")
    assert admin_checker(current_user=admin) == admin
