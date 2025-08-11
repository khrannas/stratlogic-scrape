"""
LLM-powered keyword expansion and content analysis.
"""

import json
import logging
from typing import List, Dict, Any, Optional
import aiohttp
from .config import WebScraperSettings


class LLMService:
    """Service for interacting with LLM providers."""
    
    def __init__(self, settings: WebScraperSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def generate_text(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate text using the configured LLM provider."""
        if self.settings.llm_provider == "openrouter":
            return await self._generate_openrouter(prompt, max_tokens)
        elif self.settings.llm_provider == "gemini":
            return await self._generate_gemini(prompt, max_tokens)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.settings.llm_provider}")
    
    async def _generate_openrouter(self, prompt: str, max_tokens: int) -> str:
        """Generate text using OpenRouter API."""
        if not self.settings.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://stratlogic.com",
            "X-Title": "StratLogic Web Scraper"
        }
        
        data = {
            "model": "anthropic/claude-3-sonnet",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        try:
            async with self.session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    self.logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                    raise Exception(f"OpenRouter API error: {response.status}")
        except Exception as e:
            self.logger.error(f"OpenRouter request failed: {e}")
            raise
    
    async def _generate_gemini(self, prompt: str, max_tokens: int) -> str:
        """Generate text using Google Gemini API."""
        if not self.settings.gemini_api_key:
            raise ValueError("Gemini API key not configured")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.settings.gemini_api_key}"
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.7
            }
        }
        
        try:
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    error_text = await response.text()
                    self.logger.error(f"Gemini API error: {response.status} - {error_text}")
                    raise Exception(f"Gemini API error: {response.status}")
        except Exception as e:
            self.logger.error(f"Gemini request failed: {e}")
            raise


class KeywordExpander:
    """Expands keywords using LLM for better search results."""
    
    def __init__(self, settings: WebScraperSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.llm_service = LLMService(settings)
    
    async def expand_keywords(
        self,
        keywords: List[str],
        max_expansions: int = 10,
        context: str = ""
    ) -> List[str]:
        """Expand keywords using LLM."""
        
        try:
            # Create prompt for keyword expansion
            prompt = f"""
            Given the following keywords: {', '.join(keywords)}
            
            Context: {context}
            
            Please expand these keywords with related terms, synonyms, and variations that would be useful for web scraping. 
            Focus on terms that would help find relevant content.
            
            Return only the expanded keywords as a comma-separated list, without numbering or additional text.
            Maximum {max_expansions} additional keywords.
            """
            
            async with self.llm_service:
                response = await self.llm_service.generate_text(prompt)
            
            # Parse response
            expanded_keywords = [
                keyword.strip() 
                for keyword in response.split(',') 
                if keyword.strip()
            ]
            
            # Combine original and expanded keywords
            all_keywords = list(set(keywords + expanded_keywords))
            
            self.logger.info(f"Expanded {len(keywords)} keywords to {len(all_keywords)} total keywords")
            return all_keywords[:max_expansions + len(keywords)]
            
        except Exception as e:
            self.logger.error(f"Keyword expansion failed: {e}")
            return keywords
    
    async def analyze_content(
        self,
        content: str,
        max_length: int = 1000
    ) -> Dict[str, Any]:
        """Analyze content using LLM."""
        
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
                "language": "lang",
                "quality_score": 8,
                "entities": ["entity1", "entity2"],
                "summary": "summary text"
            }}
            """
            
            async with self.llm_service:
                response = await self.llm_service.generate_text(prompt)
            
            # Parse JSON response
            analysis = json.loads(response)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Content analysis failed: {e}")
            return {
                "topics": [],
                "content_type": "unknown",
                "language": "en",
                "quality_score": 5,
                "entities": [],
                "summary": "Analysis failed"
            }
    
    async def classify_content(
        self,
        title: str,
        description: str,
        text_content: str
    ) -> Dict[str, Any]:
        """Classify content based on title, description, and text."""
        
        try:
            # Combine content for classification
            combined_content = f"Title: {title}\nDescription: {description}\nContent: {text_content[:500]}"
            
            prompt = f"""
            Classify the following web content:
            
            {combined_content}
            
            Return as JSON with the following structure:
            {{
                "category": "main_category",
                "subcategory": "subcategory",
                "topics": ["topic1", "topic2"],
                "sentiment": "positive|negative|neutral",
                "relevance_score": 0.85,
                "content_quality": "high|medium|low"
            }}
            """
            
            async with self.llm_service:
                response = await self.llm_service.generate_text(prompt)
            
            # Parse JSON response
            classification = json.loads(response)
            
            return classification
            
        except Exception as e:
            self.logger.error(f"Content classification failed: {e}")
            return {
                "category": "unknown",
                "subcategory": "unknown",
                "topics": [],
                "sentiment": "neutral",
                "relevance_score": 0.5,
                "content_quality": "medium"
            }
    
    async def extract_key_phrases(
        self,
        text_content: str,
        max_phrases: int = 10
    ) -> List[str]:
        """Extract key phrases from content."""
        
        try:
            prompt = f"""
            Extract the most important key phrases from the following text:
            
            {text_content[:1000]}
            
            Return only the key phrases as a comma-separated list, without numbering.
            Maximum {max_phrases} phrases.
            """
            
            async with self.llm_service:
                response = await self.llm_service.generate_text(prompt)
            
            # Parse response
            key_phrases = [
                phrase.strip() 
                for phrase in response.split(',') 
                if phrase.strip()
            ]
            
            return key_phrases[:max_phrases]
            
        except Exception as e:
            self.logger.error(f"Key phrase extraction failed: {e}")
            return []
    
    async def generate_search_queries(
        self,
        keywords: List[str],
        context: str = "",
        max_queries: int = 5
    ) -> List[str]:
        """Generate optimized search queries from keywords."""
        
        try:
            prompt = f"""
            Given these keywords: {', '.join(keywords)}
            
            Context: {context}
            
            Generate {max_queries} optimized search queries that would be most effective for finding relevant web content.
            Make the queries specific and targeted.
            
            Return only the search queries, one per line, without numbering.
            """
            
            async with self.llm_service:
                response = await self.llm_service.generate_text(prompt)
            
            # Parse response
            queries = [
                query.strip() 
                for query in response.split('\n') 
                if query.strip()
            ]
            
            return queries[:max_queries]
            
        except Exception as e:
            self.logger.error(f"Search query generation failed: {e}")
            return keywords
    
    async def validate_keywords(
        self,
        keywords: List[str]
    ) -> Dict[str, bool]:
        """Validate keywords for search effectiveness."""
        
        try:
            prompt = f"""
            Evaluate these keywords for web search effectiveness: {', '.join(keywords)}
            
            For each keyword, determine if it's:
            1. Too broad (will return too many results)
            2. Too specific (will return too few results)
            3. Just right (good balance)
            
            Return as JSON with keyword as key and "broad", "specific", or "good" as value.
            """
            
            async with self.llm_service:
                response = await self.llm_service.generate_text(prompt)
            
            # Parse JSON response
            validation = json.loads(response)
            
            return validation
            
        except Exception as e:
            self.logger.error(f"Keyword validation failed: {e}")
            return {keyword: "good" for keyword in keywords}
