#!/usr/bin/env python3
"""
Simple verification script for StratLogic Scraper setup.
"""

import os
import sys
from pathlib import Path

def main():
    print("StratLogic Scraper - Setup Verification")
    print("=" * 50)
    
    # Check if we're in the right directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Check key files
    key_files = [
        ".env.example",
        "docker-compose.yml", 
        "docker-compose.application.yml",
        "docker-compose.override.yml",
        "docker-compose.prod.yml",
        "Dockerfile",
        "pyproject.toml",
        "requirements.txt",
        "src/main.py",
        "src/core/config.py",
        "src/api/middleware/cors.py",
        "src/api/middleware/error_handling.py",
        "docs/development-setup.md",
        "docs/docker-setup.md"
    ]
    
    print("Checking key files...")
    for file_path in key_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
    
    # Check key directories
    key_dirs = [
        "src",
        "src/api",
        "src/api/middleware", 
        "src/core",
        "src/scrapers",
        "src/storage",
        "src/services",
        "tests",
        "docs",
        "migrations",
        "scripts"
    ]
    
    print("\nChecking key directories...")
    for dir_path in key_dirs:
        if Path(dir_path).exists():
            print(f"✓ {dir_path}/")
        else:
            print(f"✗ {dir_path}/ - MISSING")
    
    # Check Python packages
    print("\nChecking Python packages...")
    packages = [
        "fastapi",
        "uvicorn", 
        "sqlalchemy",
        "psycopg2-binary",
        "redis",
        "minio",
        "playwright",
        "pydantic"
    ]
    
    for package in packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NOT INSTALLED")
    
    print("\n" + "=" * 50)
    print("Setup verification complete!")
    print("\nNext steps:")
    print("1. Start Docker Desktop")
    print("2. Run: docker-compose up -d")
    print("3. Run: uvicorn src.main:app --reload")
    print("4. Visit: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
