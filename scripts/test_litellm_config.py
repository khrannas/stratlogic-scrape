#!/usr/bin/env python3
"""
Test script to verify LiteLLM configuration is working properly
"""

import os
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.config import settings
from src.services.llm_service import LLMService

async def test_litellm_configuration():
    """Test the LiteLLM configuration"""
    print("Testing LiteLLM Configuration...")
    print("=" * 50)

    # Check configuration
    print(f"LLM Provider: {settings.LLM_PROVIDER}")
    print(f"Use LiteLLM Proxy: {settings.USE_LITELLM_PROXY}")
    print(f"LiteLLM Proxy URL: {settings.LITELLM_PROXY_URL}")
    print(f"OpenRouter API Key: {'Set' if settings.OPENROUTER_API_KEY else 'Not Set'}")
    print()

    # Initialize LLM Service
    try:
        llm_service = LLMService()
        print("✅ LLM Service initialized successfully")
        print(f"Default model for {settings.LLM_PROVIDER}: {llm_service.default_models.get(settings.LLM_PROVIDER, 'Unknown')}")
        print()

        # Test a simple text generation
        if settings.OPENROUTER_API_KEY:
            print("Testing text generation...")
            try:
                response = await llm_service.generate_text(
                    prompt="Hello, this is a test message. Please respond with 'Test successful!'",
                    max_tokens=50,
                    temperature=0.1
                )
                print(f"✅ Text generation successful: {response[:100]}...")
            except Exception as e:
                print(f"❌ Text generation failed: {e}")
        else:
            print("⚠️  OpenRouter API key not set - skipping text generation test")

    except Exception as e:
        print(f"❌ LLM Service initialization failed: {e}")

    print("=" * 50)
    print("Configuration test completed!")

if __name__ == "__main__":
    asyncio.run(test_litellm_configuration())
