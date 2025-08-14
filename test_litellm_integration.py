#!/usr/bin/env python3
"""
Test script to verify LiteLLM integration
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services.llm_service import llm_service

async def test_litellm_integration():
    """Test the LiteLLM integration"""
    print("Testing LiteLLM Integration...")
    print("=" * 50)

    # Test provider info
    provider_info = llm_service.get_provider_info()
    print(f"Provider: {provider_info['provider']}")
    print(f"Default Model: {provider_info['default_model']}")
    print(f"Using Proxy: {provider_info['using_proxy']}")
    print(f"Available Providers: {provider_info['available_providers']}")
    print()

    # Test simple text generation
    try:
        print("Testing text generation...")
        response = await llm_service.generate_text(
            prompt="Hello! Please respond with a short greeting.",
            max_tokens=50,
            temperature=0.7
        )
        print(f"Response: {response}")
        print("✅ Text generation successful!")
    except Exception as e:
        print(f"❌ Text generation failed: {e}")

    print()

    # Test keyword expansion
    try:
        print("Testing keyword expansion...")
        keywords = ["machine learning", "artificial intelligence"]
        expanded = await llm_service.expand_keywords(keywords, max_expansions=5)
        print(f"Original keywords: {keywords}")
        print(f"Expanded keywords: {expanded}")
        print("✅ Keyword expansion successful!")
    except Exception as e:
        print(f"❌ Keyword expansion failed: {e}")

    print()

    # Test content analysis
    try:
        print("Testing content analysis...")
        content = "This is a sample text about artificial intelligence and machine learning."
        analysis = await llm_service.analyze_content(content)
        print(f"Analysis: {analysis}")
        print("✅ Content analysis successful!")
    except Exception as e:
        print(f"❌ Content analysis failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_litellm_integration())
