"""
Content analyzer for LLM-powered paper analysis.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import hashlib
import json
import re
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    """Result of paper content analysis."""
    summary: str
    keywords: List[str]
    topics: List[str]
    quality_score: float
    language: str
    content_type: str
    key_phrases: List[str]
    entities: List[Dict[str, Any]]
    sentiment: str
    complexity_score: float
    citation_analysis: Dict[str, Any]
    recommendations: List[str]


class PaperContentAnalyzer:
    """Analyzer for paper content using LLM and NLP techniques."""
    
    def __init__(self, config, llm_service=None):
        self.config = config
        self.llm_service = llm_service
        self.logger = logging.getLogger(__name__)
    
    async def analyze_paper(
        self,
        paper_data: Dict[str, Any],
        include_citations: bool = True,
        include_recommendations: bool = True
    ) -> Optional[AnalysisResult]:
        """
        Perform comprehensive analysis of a paper.
        
        Args:
            paper_data: Paper metadata and content
            include_citations: Whether to analyze citations
            include_recommendations: Whether to generate recommendations
            
        Returns:
            AnalysisResult object with analysis data
        """
        try:
            self.logger.info(f"Analyzing paper: {paper_data.get('title', 'Unknown')}")
            
            # Extract content for analysis
            content = self._extract_content_for_analysis(paper_data)
            if not content:
                self.logger.warning("No content available for analysis")
                return None
            
            # Perform analysis tasks
            analysis_tasks = [
                self._generate_summary(content),
                self._extract_keywords(content),
                self._identify_topics(content),
                self._assess_quality(content),
                self._detect_language(content),
                self._classify_content_type(content),
                self._extract_key_phrases(content),
                self._extract_entities(content),
                self._analyze_sentiment(content),
                self._assess_complexity(content)
            ]
            
            # Execute analysis tasks
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Process results
            summary = results[0] if not isinstance(results[0], Exception) else ""
            keywords = results[1] if not isinstance(results[1], Exception) else []
            topics = results[2] if not isinstance(results[2], Exception) else []
            quality_score = results[3] if not isinstance(results[3], Exception) else 0.5
            language = results[4] if not isinstance(results[4], Exception) else "en"
            content_type = results[5] if not isinstance(results[5], Exception) else "research"
            key_phrases = results[6] if not isinstance(results[6], Exception) else []
            entities = results[7] if not isinstance(results[7], Exception) else []
            sentiment = results[8] if not isinstance(results[8], Exception) else "neutral"
            complexity_score = results[9] if not isinstance(results[9], Exception) else 0.5
            
            # Analyze citations if requested
            citation_analysis = {}
            if include_citations and paper_data.get('citations'):
                citation_analysis = await self._analyze_citations(paper_data['citations'])
            
            # Generate recommendations if requested
            recommendations = []
            if include_recommendations:
                recommendations = await self._generate_recommendations(
                    paper_data, topics, keywords, quality_score
                )
            
            return AnalysisResult(
                summary=summary,
                keywords=keywords,
                topics=topics,
                quality_score=quality_score,
                language=language,
                content_type=content_type,
                key_phrases=key_phrases,
                entities=entities,
                sentiment=sentiment,
                complexity_score=complexity_score,
                citation_analysis=citation_analysis,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Paper analysis failed: {e}")
            return None
    
    def _extract_content_for_analysis(self, paper_data: Dict[str, Any]) -> str:
        """
        Extract and prepare content for analysis.
        
        Args:
            paper_data: Paper metadata and content
            
        Returns:
            Combined content string for analysis
        """
        try:
            content_parts = []
            
            # Add title
            if paper_data.get('title'):
                content_parts.append(f"Title: {paper_data['title']}")
            
            # Add abstract
            if paper_data.get('abstract'):
                content_parts.append(f"Abstract: {paper_data['abstract']}")
            elif paper_data.get('summary'):
                content_parts.append(f"Summary: {paper_data['summary']}")
            
            # Add main text content
            if paper_data.get('body', {}).get('text'):
                # Truncate to avoid token limits
                text = paper_data['body']['text']
                if len(text) > self.config.max_content_length:
                    text = text[:self.config.max_content_length] + "..."
                content_parts.append(f"Content: {text}")
            
            # Add keywords if available
            if paper_data.get('keywords'):
                content_parts.append(f"Keywords: {', '.join(paper_data['keywords'])}")
            
            return "\n\n".join(content_parts)
            
        except Exception as e:
            self.logger.error(f"Failed to extract content: {e}")
            return ""
    
    async def _generate_summary(self, content: str) -> str:
        """
        Generate a summary of the paper content.
        
        Args:
            content: Paper content to summarize
            
        Returns:
            Generated summary
        """
        try:
            if not self.llm_service:
                return self._fallback_summary(content)
            
            prompt = f"""
            Please provide a concise summary of the following academic paper content.
            Focus on the main findings, methodology, and conclusions.
            Keep the summary to 2-3 sentences.
            
            Content:
            {content[:2000]}  # Limit content length
            
            Summary:
            """
            
            response = await self.llm_service.generate_text(prompt)
            return response.strip() if response else self._fallback_summary(content)
            
        except Exception as e:
            self.logger.error(f"Summary generation failed: {e}")
            return self._fallback_summary(content)
    
    async def _extract_keywords(self, content: str) -> List[str]:
        """
        Extract keywords from the paper content.
        
        Args:
            content: Paper content
            
        Returns:
            List of extracted keywords
        """
        try:
            if not self.llm_service:
                return self._fallback_keywords(content)
            
            prompt = f"""
            Extract 10-15 most important keywords from the following academic paper content.
            Focus on technical terms, concepts, and domain-specific vocabulary.
            Return only the keywords as a comma-separated list, without numbering or additional text.
            
            Content:
            {content[:1500]}
            
            Keywords:
            """
            
            response = await self.llm_service.generate_text(prompt)
            if response:
                keywords = [kw.strip() for kw in response.split(',') if kw.strip()]
                return keywords[:15]  # Limit to 15 keywords
            
            return self._fallback_keywords(content)
            
        except Exception as e:
            self.logger.error(f"Keyword extraction failed: {e}")
            return self._fallback_keywords(content)
    
    async def _identify_topics(self, content: str) -> List[str]:
        """
        Identify main topics and themes in the paper.
        
        Args:
            content: Paper content
            
        Returns:
            List of identified topics
        """
        try:
            if not self.llm_service:
                return self._fallback_topics(content)
            
            prompt = f"""
            Identify the main topics and themes discussed in the following academic paper.
            Focus on broad subject areas, research domains, and key themes.
            Return 5-8 topics as a comma-separated list.
            
            Content:
            {content[:1500]}
            
            Topics:
            """
            
            response = await self.llm_service.generate_text(prompt)
            if response:
                topics = [topic.strip() for topic in response.split(',') if topic.strip()]
                return topics[:8]  # Limit to 8 topics
            
            return self._fallback_topics(content)
            
        except Exception as e:
            self.logger.error(f"Topic identification failed: {e}")
            return self._fallback_topics(content)
    
    async def _assess_quality(self, content: str) -> float:
        """
        Assess the quality of the paper content.
        
        Args:
            content: Paper content
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        try:
            if not self.llm_service:
                return self._fallback_quality_score(content)
            
            prompt = f"""
            Assess the quality of the following academic paper content.
            Consider factors like clarity, completeness, technical depth, and academic rigor.
            Return a score between 0.0 and 1.0, where 1.0 is highest quality.
            Return only the numerical score.
            
            Content:
            {content[:1500]}
            
            Quality Score:
            """
            
            response = await self.llm_service.generate_text(prompt)
            if response:
                try:
                    score = float(response.strip())
                    return max(0.0, min(1.0, score))  # Clamp between 0 and 1
                except ValueError:
                    pass
            
            return self._fallback_quality_score(content)
            
        except Exception as e:
            self.logger.error(f"Quality assessment failed: {e}")
            return self._fallback_quality_score(content)
    
    async def _detect_language(self, content: str) -> str:
        """
        Detect the language of the paper content.
        
        Args:
            content: Paper content
            
        Returns:
            Language code (e.g., 'en', 'es', 'fr')
        """
        try:
            if not self.llm_service:
                return self._fallback_language_detection(content)
            
            prompt = f"""
            Detect the language of the following text.
            Return only the ISO 639-1 language code (e.g., 'en' for English, 'es' for Spanish).
            
            Text:
            {content[:500]}
            
            Language Code:
            """
            
            response = await self.llm_service.generate_text(prompt)
            if response:
                lang_code = response.strip().lower()
                if len(lang_code) == 2:
                    return lang_code
            
            return self._fallback_language_detection(content)
            
        except Exception as e:
            self.logger.error(f"Language detection failed: {e}")
            return self._fallback_language_detection(content)
    
    async def _classify_content_type(self, content: str) -> str:
        """
        Classify the type of academic content.
        
        Args:
            content: Paper content
            
        Returns:
            Content type classification
        """
        try:
            if not self.llm_service:
                return self._fallback_content_type(content)
            
            prompt = f"""
            Classify the type of academic content in the following text.
            Choose from: research_paper, review_paper, case_study, methodology, survey, 
            technical_report, conference_paper, thesis, dissertation, book_chapter.
            Return only the classification.
            
            Content:
            {content[:1000]}
            
            Content Type:
            """
            
            response = await self.llm_service.generate_text(prompt)
            if response:
                content_type = response.strip().lower()
                valid_types = [
                    'research_paper', 'review_paper', 'case_study', 'methodology',
                    'survey', 'technical_report', 'conference_paper', 'thesis',
                    'dissertation', 'book_chapter'
                ]
                if content_type in valid_types:
                    return content_type
            
            return self._fallback_content_type(content)
            
        except Exception as e:
            self.logger.error(f"Content type classification failed: {e}")
            return self._fallback_content_type(content)
    
    async def _extract_key_phrases(self, content: str) -> List[str]:
        """
        Extract key phrases from the content.
        
        Args:
            content: Paper content
            
        Returns:
            List of key phrases
        """
        try:
            if not self.llm_service:
                return self._fallback_key_phrases(content)
            
            prompt = f"""
            Extract 5-10 key phrases from the following academic content.
            Focus on important concepts, findings, and technical terms.
            Return only the phrases as a comma-separated list.
            
            Content:
            {content[:1500]}
            
            Key Phrases:
            """
            
            response = await self.llm_service.generate_text(prompt)
            if response:
                phrases = [phrase.strip() for phrase in response.split(',') if phrase.strip()]
                return phrases[:10]  # Limit to 10 phrases
            
            return self._fallback_key_phrases(content)
            
        except Exception as e:
            self.logger.error(f"Key phrase extraction failed: {e}")
            return self._fallback_key_phrases(content)
    
    async def _extract_entities(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from the content.
        
        Args:
            content: Paper content
            
        Returns:
            List of extracted entities
        """
        try:
            if not self.llm_service:
                return self._fallback_entities(content)
            
            prompt = f"""
            Extract named entities from the following academic content.
            Include people, organizations, locations, dates, and technical terms.
            Return as JSON array with 'text', 'type', and 'confidence' fields.
            
            Content:
            {content[:1500]}
            
            Entities:
            """
            
            response = await self.llm_service.generate_text(prompt)
            if response:
                try:
                    entities = json.loads(response)
                    if isinstance(entities, list):
                        return entities[:20]  # Limit to 20 entities
                except json.JSONDecodeError:
                    pass
            
            return self._fallback_entities(content)
            
        except Exception as e:
            self.logger.error(f"Entity extraction failed: {e}")
            return self._fallback_entities(content)
    
    async def _analyze_sentiment(self, content: str) -> str:
        """
        Analyze the sentiment of the content.
        
        Args:
            content: Paper content
            
        Returns:
            Sentiment classification ('positive', 'negative', 'neutral')
        """
        try:
            if not self.llm_service:
                return self._fallback_sentiment(content)
            
            prompt = f"""
            Analyze the sentiment of the following academic content.
            Consider the tone, attitude, and emotional content.
            Return only: positive, negative, or neutral.
            
            Content:
            {content[:1000]}
            
            Sentiment:
            """
            
            response = await self.llm_service.generate_text(prompt)
            if response:
                sentiment = response.strip().lower()
                if sentiment in ['positive', 'negative', 'neutral']:
                    return sentiment
            
            return self._fallback_sentiment(content)
            
        except Exception as e:
            self.logger.error(f"Sentiment analysis failed: {e}")
            return self._fallback_sentiment(content)
    
    async def _assess_complexity(self, content: str) -> float:
        """
        Assess the complexity of the content.
        
        Args:
            content: Paper content
            
        Returns:
            Complexity score between 0.0 and 1.0
        """
        try:
            if not self.llm_service:
                return self._fallback_complexity_score(content)
            
            prompt = f"""
            Assess the complexity of the following academic content.
            Consider factors like vocabulary difficulty, sentence structure, and technical depth.
            Return a score between 0.0 and 1.0, where 1.0 is most complex.
            Return only the numerical score.
            
            Content:
            {content[:1000]}
            
            Complexity Score:
            """
            
            response = await self.llm_service.generate_text(prompt)
            if response:
                try:
                    score = float(response.strip())
                    return max(0.0, min(1.0, score))  # Clamp between 0 and 1
                except ValueError:
                    pass
            
            return self._fallback_complexity_score(content)
            
        except Exception as e:
            self.logger.error(f"Complexity assessment failed: {e}")
            return self._fallback_complexity_score(content)
    
    async def _analyze_citations(self, citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze citation patterns and metadata.
        
        Args:
            citations: List of citation data
            
        Returns:
            Citation analysis results
        """
        try:
            analysis = {
                'total_citations': len(citations),
                'citation_years': [],
                'citation_journals': [],
                'citation_authors': [],
                'recent_citations': 0,
                'high_impact_citations': 0
            }
            
            current_year = datetime.now().year
            
            for citation in citations:
                # Extract year
                if citation.get('year'):
                    analysis['citation_years'].append(citation['year'])
                    if citation['year'] >= current_year - 5:
                        analysis['recent_citations'] += 1
                
                # Extract journal
                if citation.get('journal'):
                    analysis['citation_journals'].append(citation['journal'])
                
                # Extract authors
                if citation.get('authors'):
                    analysis['citation_authors'].extend(citation['authors'])
            
            # Calculate statistics
            if analysis['citation_years']:
                analysis['avg_citation_year'] = sum(analysis['citation_years']) / len(analysis['citation_years'])
                analysis['oldest_citation'] = min(analysis['citation_years'])
                analysis['newest_citation'] = max(analysis['citation_years'])
            
            # Count unique journals and authors
            analysis['unique_journals'] = len(set(analysis['citation_journals']))
            analysis['unique_authors'] = len(set(analysis['citation_authors']))
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Citation analysis failed: {e}")
            return {}
    
    async def _generate_recommendations(
        self,
        paper_data: Dict[str, Any],
        topics: List[str],
        keywords: List[str],
        quality_score: float
    ) -> List[str]:
        """
        Generate recommendations based on paper analysis.
        
        Args:
            paper_data: Paper metadata
            topics: Identified topics
            keywords: Extracted keywords
            quality_score: Quality assessment score
            
        Returns:
            List of recommendations
        """
        try:
            recommendations = []
            
            # Quality-based recommendations
            if quality_score < 0.5:
                recommendations.append("Consider improving clarity and structure")
                recommendations.append("Add more detailed methodology section")
            
            if quality_score > 0.8:
                recommendations.append("High-quality paper suitable for top-tier journals")
            
            # Topic-based recommendations
            if topics:
                recommendations.append(f"Related topics to explore: {', '.join(topics[:3])}")
            
            # Keyword-based recommendations
            if keywords:
                recommendations.append(f"Key areas for further research: {', '.join(keywords[:5])}")
            
            # Citation-based recommendations
            if paper_data.get('citations'):
                citation_count = len(paper_data['citations'])
                if citation_count < 10:
                    recommendations.append("Consider adding more recent citations")
                elif citation_count > 50:
                    recommendations.append("Paper has comprehensive citation coverage")
            
            return recommendations[:5]  # Limit to 5 recommendations
            
        except Exception as e:
            self.logger.error(f"Recommendation generation failed: {e}")
            return []
    
    # Fallback methods for when LLM service is not available
    def _fallback_summary(self, content: str) -> str:
        """Fallback summary generation."""
        sentences = content.split('.')[:3]
        return '. '.join(sentences) + '.'
    
    def _fallback_keywords(self, content: str) -> List[str]:
        """Fallback keyword extraction."""
        words = re.findall(r'\b\w+\b', content.lower())
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1
        return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def _fallback_topics(self, content: str) -> List[str]:
        """Fallback topic identification."""
        return ["academic research", "scientific study", "technical analysis"]
    
    def _fallback_quality_score(self, content: str) -> float:
        """Fallback quality assessment."""
        return 0.7  # Default moderate quality
    
    def _fallback_language_detection(self, content: str) -> str:
        """Fallback language detection."""
        return "en"  # Default to English
    
    def _fallback_content_type(self, content: str) -> str:
        """Fallback content type classification."""
        return "research_paper"
    
    def _fallback_key_phrases(self, content: str) -> List[str]:
        """Fallback key phrase extraction."""
        return ["academic content", "research findings", "methodology"]
    
    def _fallback_entities(self, content: str) -> List[Dict[str, Any]]:
        """Fallback entity extraction."""
        return []
    
    def _fallback_sentiment(self, content: str) -> str:
        """Fallback sentiment analysis."""
        return "neutral"
    
    def _fallback_complexity_score(self, content: str) -> float:
        """Fallback complexity assessment."""
        return 0.6  # Default moderate complexity
