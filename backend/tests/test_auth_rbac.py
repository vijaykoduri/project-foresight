import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException, status
from app.core.security import create_access_token, decode_access_token
from app.api.deps import get_current_user, require_roles
from app.models.user import User, Role

def test_jwt_role_encoding_decoding():
    # Test encoding role into JWT token
    data = {"sub": "123", "role": "admin"}
    token = create_access_token(data)
    
    # Test decoding role from JWT token
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded.get("sub") == "123"
    assert decoded.get("role") == "admin"

def test_get_current_user_jwt_role():
    # Mock database session and query
    db_mock = MagicMock()
    user_mock = User(id=123, email="test@example.com", is_active=True)
    user_mock.role = Role(name="user") # db role is user
    
    db_mock.query().filter().first.return_value = user_mock
    
    # Create credentials with admin role in JWT
    token_data = {"sub": "123", "role": "admin"}
    token = create_access_token(token_data)
    
    credentials_mock = MagicMock()
    credentials_mock.credentials = token
    
    # Call get_current_user
    current_user = get_current_user(credentials=credentials_mock, db=db_mock)
    
    # Assert jwt_role is attached to the user object
    assert current_user.jwt_role == "admin"
    assert current_user.role.name == "user" # db role is still user

def test_require_roles_success():
    # User with jwt_role admin
    user = User(id=123, email="test@example.com", is_active=True)
    user.role = Role(name="user")
    user.jwt_role = "admin"
    
    # Should not raise exception
    checker = require_roles("admin")
    result = checker(current_user=user)
    assert result == user

def test_require_roles_forbidden():
    # User with jwt_role user
    user = User(id=123, email="test@example.com", is_active=True)
    user.role = Role(name="user")
    user.jwt_role = "user"
    
    # Should raise HTTP 403 Forbidden
    checker = require_roles("admin")
    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=user)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "Insufficient permissions"
