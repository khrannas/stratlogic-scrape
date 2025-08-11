"""
Content enrichment service for the StratLogic Scraping System.

This module provides content enrichment functionality including
automatic content tagging, quality scoring, and content analysis.
"""

import hashlib
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from ..core.models.content_processing import (
    ContentEnrichment, ContentTag, ContentVersion, ContentRelationship,
    ContentType, QualityLevel, ProcessingStatus
)
from ..core.models import Artifact
from ..core.exceptions import ContentProcessingError
from ..services.logging_service import get_logger


logger = get_logger(__name__)


class ContentEnrichmentService:
    """Service for content enrichment operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def enrich_artifact(self, artifact_id: UUID) -> ContentEnrichment:
        """Enrich an artifact with comprehensive content analysis."""
        try:
            # Get artifact
            artifact = await self._get_artifact(artifact_id)
            if not artifact:
                raise ContentProcessingError(f"Artifact {artifact_id} not found")
            
            # Check if already enriched
            existing_enrichment = await self._get_existing_enrichment(artifact_id)
            if existing_enrichment:
                logger.info(f"Content enrichment already exists for artifact {artifact_id}")
                return existing_enrichment
            
            # Create content enrichment record
            content_enrichment = await self._create_enrichment_record(artifact)
            
            # Perform enrichment tasks
            await self._perform_content_analysis(content_enrichment, artifact)
            await self._perform_quality_scoring(content_enrichment, artifact)
            await self._perform_automatic_tagging(content_enrichment, artifact)
            await self._create_initial_version(content_enrichment, artifact)
            
            # Update status to completed
            content_enrichment.processing_status = ProcessingStatus.COMPLETED
            await self.db.commit()
            
            logger.info(f"Content enrichment completed for artifact {artifact_id}")
            return content_enrichment
            
        except Exception as e:
            logger.error(f"Content enrichment failed for artifact {artifact_id}", extra={"error": str(e)})
            if 'content_enrichment' in locals():
                content_enrichment.processing_status = ProcessingStatus.FAILED
                content_enrichment.error_message = str(e)
                await self.db.commit()
            raise ContentProcessingError(f"Content enrichment failed: {str(e)}")
    
    async def _get_artifact(self, artifact_id: UUID) -> Optional[Artifact]:
        """Get artifact by ID."""
        result = await self.db.execute(
            select(Artifact).where(Artifact.id == artifact_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_existing_enrichment(self, artifact_id: UUID) -> Optional[ContentEnrichment]:
        """Get existing content enrichment for artifact."""
        result = await self.db.execute(
            select(ContentEnrichment).where(ContentEnrichment.artifact_id == artifact_id)
        )
        return result.scalar_one_or_none()
    
    async def _create_enrichment_record(self, artifact: Artifact) -> ContentEnrichment:
        """Create initial content enrichment record."""
        content_type = self._determine_content_type(artifact)
        
        content_enrichment = ContentEnrichment(
            artifact_id=artifact.id,
            content_type=content_type,
            processing_status=ProcessingStatus.PROCESSING
        )
        
        self.db.add(content_enrichment)
        await self.db.flush()
        return content_enrichment
    
    def _determine_content_type(self, artifact: Artifact) -> ContentType:
        """Determine content type from artifact."""
        mime_type = artifact.mime_type or ""
        
        if "pdf" in mime_type.lower():
            return ContentType.PDF
        elif "image" in mime_type.lower():
            return ContentType.IMAGE
        elif "document" in mime_type.lower() or "word" in mime_type.lower():
            return ContentType.DOCUMENT
        elif "spreadsheet" in mime_type.lower() or "excel" in mime_type.lower():
            return ContentType.SPREADSHEET
        elif "presentation" in mime_type.lower() or "powerpoint" in mime_type.lower():
            return ContentType.PRESENTATION
        elif artifact.artifact_type.value == "paper":
            return ContentType.PAPER
        elif artifact.artifact_type.value == "government_doc":
            return ContentType.GOVERNMENT_DOC
        elif artifact.artifact_type.value == "web_page":
            return ContentType.WEBPAGE
        else:
            return ContentType.TEXT
    
    async def _perform_content_analysis(self, enrichment: ContentEnrichment, artifact: Artifact):
        """Perform basic content analysis."""
        text_content = artifact.content_text or ""
        
        # Extract text content
        enrichment.extracted_text = text_content
        
        # Analyze language
        enrichment.language = await self._detect_language(text_content)
        
        # Count words and characters
        enrichment.word_count = len(text_content.split()) if text_content else 0
        enrichment.character_count = len(text_content) if text_content else 0
        
        # Store processing metadata
        enrichment.processing_metadata = {
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "content_length": len(text_content),
            "has_content": bool(text_content)
        }
    
    async def _detect_language(self, text: str) -> Optional[str]:
        """Detect language of text content."""
        if not text:
            return None
        
        # Simple language detection based on common patterns
        text_lower = text.lower()
        
        # Check for common English words
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if english_count > 3:
            return "en"
        
        return "unknown"
    
    async def _perform_quality_scoring(self, enrichment: ContentEnrichment, artifact: Artifact):
        """Perform content quality scoring."""
        text_content = enrichment.extracted_text or ""
        
        if not text_content:
            enrichment.quality_score = 0.0
            enrichment.quality_level = QualityLevel.POOR
            return
        
        # Calculate quality metrics
        readability_score = await self._calculate_readability(text_content)
        complexity_score = await self._calculate_complexity(text_content)
        completeness_score = await self._calculate_completeness(text_content, artifact)
        
        # Overall quality score (weighted average)
        enrichment.readability_score = readability_score
        enrichment.complexity_score = complexity_score
        enrichment.quality_score = (
            readability_score * 0.3 +
            complexity_score * 0.3 +
            completeness_score * 0.4
        )
        
        # Determine quality level
        if enrichment.quality_score >= 0.8:
            enrichment.quality_level = QualityLevel.EXCELLENT
        elif enrichment.quality_score >= 0.6:
            enrichment.quality_level = QualityLevel.GOOD
        elif enrichment.quality_score >= 0.4:
            enrichment.quality_level = QualityLevel.AVERAGE
        else:
            enrichment.quality_level = QualityLevel.POOR
    
    async def _calculate_readability(self, text: str) -> float:
        """Calculate readability score using Flesch Reading Ease."""
        if not text:
            return 0.0
        
        sentences = len(re.split(r'[.!?]+', text))
        words = len(text.split())
        syllables = self._count_syllables(text)
        
        if sentences == 0 or words == 0:
            return 0.0
        
        # Flesch Reading Ease formula
        flesch_score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
        
        # Normalize to 0-1 range
        return max(0.0, min(1.0, flesch_score / 100.0))
    
    def _count_syllables(self, text: str) -> int:
        """Count syllables in text."""
        text = text.lower()
        count = 0
        vowels = "aeiouy"
        on_vowel = False
        
        for char in text:
            is_vowel = char in vowels
            if is_vowel and not on_vowel:
                count += 1
            on_vowel = is_vowel
        
        return count
    
    async def _calculate_complexity(self, text: str) -> float:
        """Calculate text complexity score."""
        if not text:
            return 0.0
        
        words = text.split()
        if not words:
            return 0.0
        
        # Calculate average word length
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Calculate unique word ratio
        unique_words = len(set(words))
        unique_ratio = unique_words / len(words)
        
        # Complexity score (higher = more complex)
        complexity = (avg_word_length / 10.0) * 0.5 + unique_ratio * 0.5
        
        # Invert so higher score = better (less complex)
        return max(0.0, min(1.0, 1.0 - complexity))
    
    async def _calculate_completeness(self, text: str, artifact: Artifact) -> float:
        """Calculate content completeness score."""
        if not text:
            return 0.0
        
        # Check for various content indicators
        indicators = {
            'has_title': bool(artifact.title),
            'has_description': bool(artifact.description),
            'has_keywords': bool(artifact.keywords),
            'has_tags': bool(artifact.tags),
            'has_summary': bool(artifact.content_summary),
            'has_content': len(text) > 100,
            'has_structure': bool(re.search(r'\n\n|\r\n\r\n', text))
        }
        
        # Calculate completeness score
        completeness = sum(indicators.values()) / len(indicators)
        return completeness
    
    async def _perform_automatic_tagging(self, enrichment: ContentEnrichment, artifact: Artifact):
        """Perform automatic content tagging."""
        text_content = enrichment.extracted_text or ""
        if not text_content:
            return
        
        # Extract tags from various sources
        tags = set()
        
        # Add existing tags from artifact
        if artifact.tags:
            tags.update(artifact.tags)
        
        # Add keywords from artifact
        if artifact.keywords:
            tags.update(artifact.keywords)
        
        # Extract tags from content using NLP
        content_tags = await self._extract_tags_from_content(text_content)
        tags.update(content_tags)
        
        # Create or get tag records
        tag_records = []
        for tag_name in tags:
            if tag_name and len(tag_name.strip()) > 0:
                tag_record = await self._get_or_create_tag(tag_name.strip())
                tag_records.append(tag_record)
        
        # Associate tags with content
        enrichment.tags = tag_records
    
    async def _extract_tags_from_content(self, text: str) -> List[str]:
        """Extract tags from text content using NLP techniques."""
        tags = set()
        
        # Extract noun phrases (simple approach)
        words = text.lower().split()
        
        # Common important words (in production, use proper NLP)
        important_words = [
            'research', 'study', 'analysis', 'report', 'data', 'information',
            'technology', 'science', 'business', 'government', 'policy',
            'development', 'innovation', 'management', 'strategy', 'solution'
        ]
        
        for word in words:
            # Clean word
            clean_word = re.sub(r'[^\w]', '', word)
            if len(clean_word) > 3 and clean_word in important_words:
                tags.add(clean_word)
        
        # Extract capitalized phrases (potential proper nouns)
        capitalized_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        for phrase in capitalized_phrases[:10]:  # Limit to first 10
            if len(phrase.split()) <= 3:  # Limit phrase length
                tags.add(phrase.lower())
        
        return list(tags)
    
    async def _get_or_create_tag(self, tag_name: str) -> ContentTag:
        """Get existing tag or create new one."""
        result = await self.db.execute(
            select(ContentTag).where(ContentTag.name == tag_name)
        )
        existing_tag = result.scalar_one_or_none()
        
        if existing_tag:
            return existing_tag
        
        # Create new tag
        new_tag = ContentTag(
            name=tag_name,
            category=self._categorize_tag(tag_name),
            confidence_score=0.8  # Default confidence
        )
        
        self.db.add(new_tag)
        await self.db.flush()
        return new_tag
    
    def _categorize_tag(self, tag_name: str) -> str:
        """Categorize tag based on content."""
        tag_lower = tag_name.lower()
        
        # Simple categorization logic
        if any(word in tag_lower for word in ['research', 'study', 'analysis']):
            return "research"
        elif any(word in tag_lower for word in ['technology', 'tech', 'software']):
            return "technology"
        elif any(word in tag_lower for word in ['business', 'management', 'strategy']):
            return "business"
        elif any(word in tag_lower for word in ['government', 'policy', 'regulation']):
            return "government"
        elif any(word in tag_lower for word in ['science', 'medical', 'health']):
            return "science"
        else:
            return "general"
    
    async def _create_initial_version(self, enrichment: ContentEnrichment, artifact: Artifact):
        """Create initial version record."""
        content_hash = self._calculate_content_hash(artifact)
        
        version = ContentVersion(
            content_id=enrichment.id,
            version_number=1,
            version_hash=content_hash,
            change_description="Initial content enrichment",
            change_metadata={
                "artifact_id": str(artifact.id),
                "content_type": enrichment.content_type.value,
                "quality_score": enrichment.quality_score
            }
        )
        
        self.db.add(version)
        await self.db.flush()
    
    def _calculate_content_hash(self, artifact: Artifact) -> str:
        """Calculate content hash for versioning."""
        content_parts = [
            artifact.content_text or "",
            artifact.title or "",
            artifact.description or "",
            str(artifact.keywords or []),
            str(artifact.tags or [])
        ]
        
        content_string = "|".join(content_parts)
        return hashlib.sha256(content_string.encode()).hexdigest()
    
    async def get_content_enrichment(self, enrichment_id: UUID) -> Optional[ContentEnrichment]:
        """Get content enrichment by ID with all relationships."""
        result = await self.db.execute(
            select(ContentEnrichment)
            .options(
                selectinload(ContentEnrichment.tags),
                selectinload(ContentEnrichment.versions),
                selectinload(ContentEnrichment.relationships)
            )
            .where(ContentEnrichment.id == enrichment_id)
        )
        return result.scalar_one_or_none()
    
    async def get_enrichments_by_artifact(self, artifact_id: UUID) -> Optional[ContentEnrichment]:
        """Get content enrichment for specific artifact."""
        result = await self.db.execute(
            select(ContentEnrichment)
            .options(
                selectinload(ContentEnrichment.tags),
                selectinload(ContentEnrichment.versions)
            )
            .where(ContentEnrichment.artifact_id == artifact_id)
        )
        return result.scalar_one_or_none()
