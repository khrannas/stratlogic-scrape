from typing import List, Dict, Any, Optional, Union
import logging
import asyncio
from datetime import datetime

# OpenAI imports
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion

# Google GenAI imports
import google.generativeai as genai
from google.generativeai import GenerativeModel

#

from src.core.config import settings

class LLMService:
    """
    Service for interacting with Large Language Models (OpenAI and Google Gemini)
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.provider = settings.LLM_PROVIDER.lower()

        # Initialize OpenAI client
        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.async_openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.openai_client = None
            self.async_openai_client = None

        # Initialize Google GenAI client
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.gemini_model = GenerativeModel('gemini-2.0-flash-001')
        else:
            self.gemini_model = None

        self.logger.info(f"LLM Service initialized with provider: {self.provider}")

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> str:
        """
        Generate text using the configured LLM provider
        """
        try:
            if self.provider == "openai" and self.openai_client:
                return await self._generate_text_openai(
                    prompt, max_tokens, temperature, model
                )
            elif self.provider == "gemini" and self.gemini_model:
                return await self._generate_text_gemini(
                    prompt, max_tokens, temperature, model
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")

        except Exception as e:
            self.logger.error(f"Text generation failed: {e}")
            raise

    async def _generate_text_openai(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> str:
        """Generate text using OpenAI"""
        model_name = model or "gpt-4o"

        response = await self.async_openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content

    async def _generate_text_gemini(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> str:
        """Generate text using Google Gemini"""
        model_name = model or "gemini-2.0-flash-001"

        # Create model instance
        genai_model = GenerativeModel(model_name)

        # Configure generation
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature
        )

        response = await genai_model.generate_content_async(
            prompt,
            generation_config=generation_config
        )

        return response.text

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
            "openai_available": self.openai_client is not None,
            "gemini_available": self.gemini_model is not None,
            "timestamp": datetime.utcnow().isoformat()
        }

# Create singleton instance
llm_service = LLMService()
