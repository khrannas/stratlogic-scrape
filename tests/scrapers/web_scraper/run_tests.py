#!/usr/bin/env python3
"""
Test runner for web scraper tests
"""

import sys
import os
import pytest
import asyncio
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def run_unit_tests():
    """Run unit tests"""
    print("Running unit tests...")

    test_files = [
        "test_playwright_manager.py",
        "test_search_engines.py",
        "test_content_extractor.py",
        "test_web_scraper_main.py",
        "test_config.py"
    ]

    for test_file in test_files:
        test_path = Path(__file__).parent / test_file
        if test_path.exists():
            print(f"\nRunning {test_file}...")
            result = pytest.main([
                str(test_path),
                "-v",
                "--tb=short",
                "--disable-warnings"
            ])
            if result != 0:
                print(f"❌ {test_file} failed")
                return False
            else:
                print(f"✅ {test_file} passed")
        else:
            print(f"⚠️  {test_file} not found")

    return True

def run_integration_tests():
    """Run integration tests"""
    print("\nRunning integration tests...")

    test_path = Path(__file__).parent / "test_integration.py"
    if test_path.exists():
        result = pytest.main([
            str(test_path),
            "-v",
            "--tb=short",
            "--disable-warnings"
        ])
        if result != 0:
            print("❌ Integration tests failed")
            return False
        else:
            print("✅ Integration tests passed")
            return True
    else:
        print("⚠️  Integration test file not found")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting web scraper test suite...")
    print("=" * 50)

    # Run unit tests
    unit_success = run_unit_tests()

    # Run integration tests
    integration_success = run_integration_tests()

    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"Unit Tests: {'✅ PASSED' if unit_success else '❌ FAILED'}")
    print(f"Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")

    if unit_success and integration_success:
        print("\n🎉 All tests passed!")
        return True
    else:
        print("\n💥 Some tests failed!")
        return False

def run_specific_test(test_name):
    """Run a specific test file"""
    test_path = Path(__file__).parent / f"test_{test_name}.py"

    if not test_path.exists():
        print(f"❌ Test file {test_path} not found")
        return False

    print(f"Running {test_name} tests...")
    result = pytest.main([
        str(test_path),
        "-v",
        "--tb=short",
        "--disable-warnings"
    ])

    return result == 0

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        success = run_all_tests()
        sys.exit(0 if success else 1)
