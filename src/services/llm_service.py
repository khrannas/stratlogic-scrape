from typing import List, Dict, Any, Optional, Union
import logging
import asyncio
from datetime import datetime
import os

# LiteLLM imports
import litellm
from litellm import completion

from src.core.config import settings

class LLMService:
    """
    Service for interacting with Large Language Models using LiteLLM
    Supports OpenAI, Google Gemini, OpenRouter, and other providers
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.provider = settings.LLM_PROVIDER.lower()

        # Set up LiteLLM environment variables
        self._setup_litellm_environment()

        # Configure default models for each provider
        self.default_models = {
            "openai": "gpt-4o",
            "gemini": "gemini-2.0-flash-001",
            "openrouter": "openrouter/gpt-4o",
            "anthropic": "claude-3-5-sonnet-20241022"
        }

        # Configure LiteLLM proxy if enabled
        if settings.USE_LITELLM_PROXY:
            litellm.api_base = settings.LITELLM_PROXY_URL
            litellm.api_key = "sk-1234"  # Master key for proxy
            self.logger.info(f"Using LiteLLM proxy at: {settings.LITELLM_PROXY_URL}")

        self.logger.info(f"LLM Service initialized with provider: {self.provider}")

    def _setup_litellm_environment(self):
        """Set up LiteLLM environment variables based on configuration"""
        # Set API keys for different providers
        if settings.OPENAI_API_KEY:
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

        if settings.OPENROUTER_API_KEY:
            os.environ["OPENROUTER_API_KEY"] = settings.OPENROUTER_API_KEY

        if settings.GOOGLE_API_KEY:
            os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
        elif settings.GEMINI_API_KEY:
            os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> str:
        """
        Generate text using the configured LLM provider via LiteLLM
        """
        try:
            # Determine the model to use
            if model:
                model_name = model
            else:
                model_name = self.default_models.get(self.provider, "gpt-4o")

            # Add provider prefix if not already present and not using proxy
            if not settings.USE_LITELLM_PROXY:
                if self.provider == "openrouter" and not model_name.startswith("openrouter/"):
                    model_name = f"openrouter/{model_name}"
                elif self.provider == "gemini" and not model_name.startswith("gemini/"):
                    model_name = f"gemini/{model_name}"

            self.logger.info(f"Generating text with model: {model_name}")

            # Use LiteLLM completion
            response = await asyncio.to_thread(
                completion,
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )

            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"Text generation failed: {e}")
            raise

    async def expand_keywords(
        self,
        keywords: List[str],
        context: str = "",
        max_expansions: int = 10
    ) -> List[str]:
        """
        Expand keywords using LLM
        """
        try:
            prompt = f"""
            Given the following keywords: {', '.join(keywords)}

            Context: {context}

            Please expand these keywords with related terms, synonyms, and variations that would be useful for web scraping.
            Focus on terms that would help find relevant content.

            Return only the expanded keywords as a comma-separated list, without numbering or additional text.
            Maximum {max_expansions} additional keywords.
            """

            response = await self.generate_text(prompt, max_tokens=500, temperature=0.3)

            # Parse response
            expanded_keywords = [
                keyword.strip()
                for keyword in response.split(',')
                if keyword.strip()
            ]

            # Combine original and expanded keywords
            all_keywords = list(set(keywords + expanded_keywords))

            return all_keywords[:max_expansions + len(keywords)]

        except Exception as e:
            self.logger.error(f"Keyword expansion failed: {e}")
            return keywords

    async def analyze_content(
        self,
        content: str,
        max_length: int = 1000
    ) -> Dict[str, Any]:
        """
        Analyze content using LLM
        """
        try:
            # Truncate content if too long
            if len(content) > max_length:
                content = content[:max_length] + "..."

            prompt = f"""
            Analyze the following web content and provide:
            1. Main topics/themes
            2. Content type (news, blog, documentation, etc.)
            3. Language
            4. Quality score (1-10)
            5. Key entities mentioned
            6. Summary (2-3 sentences)

            Content: {content}

            Return as JSON format with the following structure:
            {{
                "topics": ["topic1", "topic2"],
                "content_type": "type",
                "language": "language",
                "quality_score": 8,
                "entities": ["entity1", "entity2"],
                "summary": "summary text"
            }}
            """

            response = await self.generate_text(prompt, max_tokens=800, temperature=0.3)

            # Try to parse JSON response
            import json
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError:
                # Fallback: return basic analysis
                return {
                    "topics": [],
                    "content_type": "unknown",
                    "language": "unknown",
                    "quality_score": 5,
                    "entities": [],
                    "summary": response[:200]
                }

        except Exception as e:
            self.logger.error(f"Content analysis failed: {e}")
            return {}

    async def summarize_content(
        self,
        content: str,
        max_length: int = 500
    ) -> str:
        """
        Summarize content using LLM
        """
        try:
            prompt = f"""
            Summarize the following content in {max_length} characters or less:

            {content}

            Provide a concise summary that captures the main points.
            """

            response = await self.generate_text(prompt, max_tokens=200, temperature=0.3)
            return response[:max_length]

        except Exception as e:
            self.logger.error(f"Content summarization failed: {e}")
            return content[:max_length] if len(content) > max_length else content

    async def classify_content(
        self,
        content: str,
        categories: List[str]
    ) -> str:
        """
        Classify content into predefined categories
        """
        try:
            prompt = f"""
            Classify the following content into one of these categories: {', '.join(categories)}

            Content: {content[:500]}

            Return only the category name, nothing else.
            """

            response = await self.generate_text(prompt, max_tokens=50, temperature=0.1)
            return response.strip()

        except Exception as e:
            self.logger.error(f"Content classification failed: {e}")
            return categories[0] if categories else "unknown"

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the configured LLM provider
        """
        return {
            "provider": self.provider,
            "default_model": self.default_models.get(self.provider, "unknown"),
            "available_providers": list(self.default_models.keys()),
            "using_proxy": settings.USE_LITELLM_PROXY,
            "proxy_url": settings.LITELLM_PROXY_URL if settings.USE_LITELLM_PROXY else None,
            "timestamp": datetime.utcnow().isoformat()
        }

# Create singleton instance
llm_service = LLMService()
