#!/usr/bin/env python3
"""
Installation script for playwright-stealth integration
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    print(f"Command: {command}")

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False

def check_installation():
    """Check if playwright-stealth is properly installed"""
    print("\nChecking playwright-stealth installation...")

    try:
        import playwright_stealth
        print("✅ playwright-stealth is installed")

        # Check version
        version = getattr(playwright_stealth, '__version__', 'unknown')
        print(f"Version: {version}")

        return True
    except ImportError:
        print("❌ playwright-stealth is not installed")
        return False

def main():
    """Main installation function"""
    print("Playwright Stealth Installation Script")
    print("="*50)

    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: It appears you're not in a virtual environment")
        print("Consider activating your virtual environment first")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Installation cancelled")
            return 1

    # Install playwright-stealth
    print("\nInstalling playwright-stealth...")
    if not run_command("pip install playwright-stealth==1.0.5", "Install playwright-stealth"):
        return 1

    # Verify installation
    if not check_installation():
        return 1

    # Install playwright browsers if not already installed
    print("\nChecking Playwright browsers...")
    if not run_command("playwright install chromium", "Install Playwright Chromium browser"):
        return 1

    print("\n" + "="*50)
    print("✅ Installation completed successfully!")
    print("\nNext steps:")
    print("1. Run the test script: python scripts/test_stealth.py")
    print("2. Test the API endpoint: POST /api/v1/web-scraper/test-stealth")
    print("3. Stealth mode is enabled by default in the web scraper")

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
