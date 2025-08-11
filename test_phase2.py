#!/usr/bin/env python3
"""
Test script for Phase 2 components.
"""

import os
import sys

# Set required environment variables for testing
os.environ["SECRET_KEY"] = "test-secret-key-for-development-only"
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test"

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all Phase 2 components can be imported."""
    try:
        # Test auth module
        from src.auth import create_access_token, hash_password, verify_password
        print("✅ Auth utilities imported successfully")
        
        # Test auth models
        from src.auth.models import UserCreate, UserLogin, Token, UserResponse
        print("✅ Auth models imported successfully")
        
        # Test API dependencies
        from src.api.dependencies import get_db, get_current_user, get_current_active_user
        print("✅ API dependencies imported successfully")
        
        # Test API middleware
        from src.api.middleware import CorrelationIDMiddleware, RequestLoggingMiddleware
        print("✅ API middleware imported successfully")
        
        # Test API routes
        from src.api.routes.auth import router as auth_router
        print("✅ Auth routes imported successfully")
        
        from src.api.routes.users import router as users_router
        print("✅ User routes imported successfully")
        
        from src.api.routes.jobs import router as jobs_router
        print("✅ Job routes imported successfully")
        
        from src.api.routes.artifacts import router as artifacts_router
        print("✅ Artifact routes imported successfully")
        
        # Test repositories
        from src.core.repositories.user import UserRepository
        print("✅ User repository imported successfully")
        
        from src.core.repositories.job import JobRepository
        print("✅ Job repository imported successfully")
        
        print("\n🎉 All Phase 2 components imported successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_auth_utilities():
    """Test authentication utilities."""
    try:
        from src.auth.password import hash_password, verify_password, validate_password_strength
        
        # Test password hashing
        password = "TestPassword123"
        hashed = hash_password(password)
        assert hashed != password
        print("✅ Password hashing works")
        
        # Test password verification
        assert verify_password(password, hashed)
        print("✅ Password verification works")
        
        # Test password strength validation
        assert validate_password_strength("StrongPass123")
        assert not validate_password_strength("weak")
        print("✅ Password strength validation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Auth utilities test failed: {e}")
        return False

def test_pydantic_models():
    """Test Pydantic models."""
    try:
        from src.auth.models import UserCreate, UserLogin, Token
        
        # Test UserCreate model
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123",
            "full_name": "Test User"
        }
        user_create = UserCreate(**user_data)
        assert user_create.username == "testuser"
        print("✅ UserCreate model works")
        
        # Test UserLogin model
        login_data = {
            "username": "testuser",
            "password": "TestPass123"
        }
        user_login = UserLogin(**login_data)
        assert user_login.username == "testuser"
        print("✅ UserLogin model works")
        
        return True
        
    except Exception as e:
        print(f"❌ Pydantic models test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Phase 2 Components\n")
    
    # Run tests
    tests = [
        ("Import Test", test_imports),
        ("Auth Utilities Test", test_auth_utilities),
        ("Pydantic Models Test", test_pydantic_models),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Phase 2 is ready.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)
