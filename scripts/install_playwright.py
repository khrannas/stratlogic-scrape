#!/usr/bin/env python3
"""
Script to install Playwright browsers and check for Windows compatibility issues.
Run this script if you encounter NotImplementedError when using the web scraper.
"""

import subprocess
import sys
import platform
import os

def install_playwright_browsers():
    """Install Playwright browsers"""
    print("Installing Playwright browsers...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install"
        ], capture_output=True, text=True, check=True)
        print("✅ Playwright browsers installed successfully!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Playwright browsers: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_playwright_installation():
    """Check if Playwright is properly installed"""
    print("Checking Playwright installation...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "playwright", "--version"
        ], capture_output=True, text=True, check=True)
        print(f"✅ Playwright version: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Playwright not found: {e}")
        return False

def check_browser_installation():
    """Check if browsers are installed"""
    print("Checking browser installation...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install", "--dry-run"
        ], capture_output=True, text=True, check=True)
        print("✅ Browsers are installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Browsers not installed: {e}")
        return False

def main():
    print("=" * 60)
    print("Playwright Installation and Compatibility Check")
    print("=" * 60)

    # Check platform
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")

    # Check Playwright installation
    if not check_playwright_installation():
        print("\n❌ Playwright is not installed. Please install it first:")
        print("pip install playwright")
        return False

    # Check browser installation
    if not check_browser_installation():
        print("\n🔧 Installing browsers...")
        if not install_playwright_browsers():
            return False

    # Windows-specific checks
    if platform.system() == "Windows":
        print("\n🔍 Windows-specific compatibility checks:")

        # Check if we're in a virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("✅ Running in virtual environment")
        else:
            print("⚠️  Not running in virtual environment (this might cause issues)")

        # Check for common Windows issues
        print("\n💡 Windows Troubleshooting Tips:")
        print("1. Make sure you're running PowerShell as Administrator")
        print("2. If you get NotImplementedError, try running: playwright install")
        print("3. Check Windows Defender or antivirus isn't blocking Playwright")
        print("4. Try running: playwright install chromium")

    print("\n✅ Playwright setup complete!")
    print("\nIf you still encounter issues:")
    print("1. Restart your Python environment")
    print("2. Try running: playwright install --force")
    print("3. Check the logs for specific error messages")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
