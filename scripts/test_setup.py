#!/usr/bin/env python3
"""
Test script to verify the StratLogic Scraper setup.
Run this script to check if all components are properly configured.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    
    try:
        # Change working directory to project root
        os.chdir(Path(__file__).parent.parent)
        import src.core.config
        print("✓ Core config imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import core config: {e}")
        return False
    
    try:
        import src.core.database
        print("✓ Database module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import database module: {e}")
        return False
    
    try:
        import src.api.middleware.cors
        print("✓ CORS middleware imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import CORS middleware: {e}")
        return False
    
    try:
        import src.api.middleware.error_handling
        print("✓ Error handling middleware imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import error handling middleware: {e}")
        return False
    
    return True

def test_configuration():
    """Test if configuration can be loaded."""
    print("\nTesting configuration...")
    
    try:
        from src.core.config import settings
        print("✓ Configuration loaded successfully")
        print(f"  - API V1 STR: {settings.API_V1_STR}")
        print(f"  - Database: {settings.POSTGRES_DB}")
        print(f"  - Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        print(f"  - MinIO: {settings.MINIO_ENDPOINT}")
        return True
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False

def test_environment_file():
    """Test if .env.example exists."""
    print("\nTesting environment file...")
    
    env_example = Path(".env.example")
    if env_example.exists():
        print("✓ .env.example file exists")
        return True
    else:
        print("✗ .env.example file not found")
        return False

def test_project_structure():
    """Test if required directories exist."""
    print("\nTesting project structure...")
    
    required_dirs = [
        "src",
        "src/api",
        "src/api/middleware",
        "src/core",
        "src/scrapers",
        "src/storage",
        "src/services",
        "tests",
        "docs",
        "migrations"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✓ {dir_path}/ exists")
        else:
            print(f"✗ {dir_path}/ missing")
            all_exist = False
    
    return all_exist

def test_docker_files():
    """Test if Docker files exist."""
    print("\nTesting Docker files...")
    
    docker_files = ["Dockerfile", "docker-compose.yml"]
    all_exist = True
    
    for file_path in docker_files:
        if Path(file_path).exists():
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_dependencies():
    """Test if required Python packages are available."""
    print("\nTesting dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "psycopg2-binary",
        "redis",
        "minio",
        "playwright",
        "pydantic"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} available")
        except ImportError:
            print(f"✗ {package} not available")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Run all tests."""
    print("StratLogic Scraper - Setup Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_configuration,
        test_environment_file,
        test_project_structure,
        test_docker_files,
        test_dependencies
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Setup is complete.")
        print("\nNext steps:")
        print("1. Start Docker Desktop")
        print("2. Run: docker-compose up -d")
        print("3. Run: uvicorn src.main:app --reload")
        print("4. Visit: http://localhost:8000/docs")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
