"""
Analytics service for the StratLogic Scraping System.

This module provides content analytics functionality including
trend analysis, source analytics, impact scoring, and content recommendations.
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload

from ..core.models.content_processing import (
    ContentAnalytics, ContentTrend, ContentRecommendation,
    ContentEnrichment, ContentType, QualityLevel
)
from ..core.models import Artifact, User
from ..core.exceptions import ContentProcessingError
from ..services.logging_service import get_logger


logger = get_logger(__name__)


class AnalyticsService:
    """Service for content analytics operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_content_analytics(self, content_enrichment_id: UUID) -> ContentAnalytics:
        """Create analytics record for content enrichment."""
        try:
            # Check if analytics already exists
            existing_analytics = await self._get_existing_analytics(content_enrichment_id)
            if existing_analytics:
                logger.info(f"Analytics already exists for content {content_enrichment_id}")
                return existing_analytics
            
            # Get content enrichment
            enrichment = await self._get_content_enrichment(content_enrichment_id)
            if not enrichment:
                raise ContentProcessingError(f"Content enrichment {content_enrichment_id} not found")
            
            # Create analytics record
            analytics = ContentAnalytics(
                content_id=content_enrichment_id
            )
            
            self.db.add(analytics)
            await self.db.flush()
            
            # Calculate initial metrics
            await self._calculate_impact_metrics(analytics, enrichment)
            await self._create_initial_trends(analytics, enrichment)
            await self._generate_recommendations(analytics, enrichment)
            
            await self.db.commit()
            
            logger.info(f"Content analytics created for content {content_enrichment_id}")
            return analytics
            
        except Exception as e:
            logger.error(f"Analytics creation failed for content {content_enrichment_id}", extra={"error": str(e)})
            raise ContentProcessingError(f"Analytics creation failed: {str(e)}")
    
    async def _get_existing_analytics(self, content_id: UUID) -> Optional[ContentAnalytics]:
        """Get existing analytics for content."""
        result = await self.db.execute(
            select(ContentAnalytics)
            .options(
                selectinload(ContentAnalytics.trends),
                selectinload(ContentAnalytics.recommendations)
            )
            .where(ContentAnalytics.content_id == content_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_content_enrichment(self, enrichment_id: UUID) -> Optional[ContentEnrichment]:
        """Get content enrichment by ID."""
        result = await self.db.execute(
            select(ContentEnrichment).where(ContentEnrichment.id == enrichment_id)
        )
        return result.scalar_one_or_none()
    
    async def _calculate_impact_metrics(self, analytics: ContentAnalytics, enrichment: ContentEnrichment):
        """Calculate impact metrics for content."""
        # Calculate relevance score based on content quality and type
        relevance_score = await self._calculate_relevance_score(enrichment)
        
        # Calculate popularity score based on usage patterns
        popularity_score = await self._calculate_popularity_score(analytics)
        
        # Calculate overall impact score
        impact_score = (relevance_score * 0.6) + (popularity_score * 0.4)
        
        # Update analytics
        analytics.relevance_score = relevance_score
        analytics.popularity_score = popularity_score
        analytics.impact_score = impact_score
        
        await self.db.flush()
    
    async def _calculate_relevance_score(self, enrichment: ContentEnrichment) -> float:
        """Calculate relevance score based on content characteristics."""
        score = 0.0
        
        # Quality factor
        if enrichment.quality_score:
            score += enrichment.quality_score * 0.3
        
        # Content length factor
        if enrichment.word_count:
            # Prefer medium-length content (not too short, not too long)
            word_count = enrichment.word_count
            if 100 <= word_count <= 5000:
                length_score = 1.0
            elif word_count < 100:
                length_score = word_count / 100
            else:
                length_score = max(0.5, 1.0 - (word_count - 5000) / 10000)
            score += length_score * 0.2
        
        # Content type factor
        type_scores = {
            ContentType.RESEARCH_PAPER: 0.9,
            ContentType.GOVERNMENT_DOC: 0.8,
            ContentType.PAPER: 0.8,
            ContentType.DOCUMENT: 0.7,
            ContentType.PDF: 0.6,
            ContentType.WEBPAGE: 0.5,
            ContentType.TEXT: 0.4,
            ContentType.IMAGE: 0.3,
            ContentType.SPREADSHEET: 0.6,
            ContentType.PRESENTATION: 0.5
        }
        type_score = type_scores.get(enrichment.content_type, 0.5)
        score += type_score * 0.2
        
        # Language factor (prefer English)
        if enrichment.language == "en":
            score += 0.1
        
        # Completeness factor
        completeness_factors = []
        if enrichment.extracted_text:
            completeness_factors.append(1.0)
        if enrichment.word_count and enrichment.word_count > 50:
            completeness_factors.append(1.0)
        if enrichment.character_count and enrichment.character_count > 200:
            completeness_factors.append(1.0)
        
        completeness_score = sum(completeness_factors) / len(completeness_factors) if completeness_factors else 0.0
        score += completeness_score * 0.2
        
        return min(1.0, score)
    
    async def _calculate_popularity_score(self, analytics: ContentAnalytics) -> float:
        """Calculate popularity score based on usage metrics."""
        score = 0.0
        
        # View count factor
        view_score = min(1.0, analytics.view_count / 100)  # Normalize to 100 views
        score += view_score * 0.4
        
        # Download count factor
        download_score = min(1.0, analytics.download_count / 50)  # Normalize to 50 downloads
        score += download_score * 0.3
        
        # Share count factor
        share_score = min(1.0, analytics.share_count / 20)  # Normalize to 20 shares
        score += share_score * 0.3
        
        return score
    
    async def _create_initial_trends(self, analytics: ContentAnalytics, enrichment: ContentEnrichment):
        """Create initial trend records for content."""
        # Create popularity trend
        popularity_trend = ContentTrend(
            analytics_id=analytics.id,
            trend_type="popularity",
            trend_value=analytics.popularity_score or 0.0,
            trend_direction="stable",
            trend_period="daily",
            time_series_data=[{
                "timestamp": time.time(),
                "value": analytics.popularity_score or 0.0
            }]
        )
        
        # Create relevance trend
        relevance_trend = ContentTrend(
            analytics_id=analytics.id,
            trend_type="relevance",
            trend_value=analytics.relevance_score or 0.0,
            trend_direction="stable",
            trend_period="daily",
            time_series_data=[{
                "timestamp": time.time(),
                "value": analytics.relevance_score or 0.0
            }]
        )
        
        # Create usage trend
        usage_trend = ContentTrend(
            analytics_id=analytics.id,
            trend_type="usage",
            trend_value=analytics.view_count,
            trend_direction="stable",
            trend_period="daily",
            time_series_data=[{
                "timestamp": time.time(),
                "value": analytics.view_count
            }]
        )
        
        self.db.add_all([popularity_trend, relevance_trend, usage_trend])
        await self.db.flush()
    
    async def _generate_recommendations(self, analytics: ContentAnalytics, enrichment: ContentEnrichment):
        """Generate content recommendations."""
        # Find similar content based on various criteria
        similar_content = await self._find_similar_content(enrichment)
        
        for i, similar_enrichment in enumerate(similar_content[:5]):  # Limit to 5 recommendations
            recommendation = ContentRecommendation(
                analytics_id=analytics.id,
                recommended_content_id=similar_enrichment['enrichment_id'],
                recommendation_score=similar_enrichment['similarity_score'],
                recommendation_reason=similar_enrichment['reason'],
                recommendation_type=similar_enrichment['type']
            )
            
            self.db.add(recommendation)
        
        await self.db.flush()
    
    async def _find_similar_content(self, enrichment: ContentEnrichment) -> List[Dict[str, Any]]:
        """Find similar content for recommendations."""
        similar_content = []
        
        # Find content with similar content type
        result = await self.db.execute(
            select(ContentEnrichment)
            .where(
                and_(
                    ContentEnrichment.id != enrichment.id,
                    ContentEnrichment.content_type == enrichment.content_type
                )
            )
            .limit(10)
        )
        
        for similar_enrichment in result.scalars().all():
            similarity_score = await self._calculate_content_similarity(enrichment, similar_enrichment)
            if similarity_score > 0.3:  # Minimum similarity threshold
                similar_content.append({
                    'enrichment_id': similar_enrichment.id,
                    'similarity_score': similarity_score,
                    'reason': f"Similar {enrichment.content_type.value} content",
                    'type': 'similar_type'
                })
        
        # Find content with similar quality level
        if enrichment.quality_level:
            result = await self.db.execute(
                select(ContentEnrichment)
                .where(
                    and_(
                        ContentEnrichment.id != enrichment.id,
                        ContentEnrichment.quality_level == enrichment.quality_level
                    )
                )
                .limit(10)
            )
            
            for similar_enrichment in result.scalars().all():
                similarity_score = await self._calculate_content_similarity(enrichment, similar_enrichment)
                if similarity_score > 0.3:
                    similar_content.append({
                        'enrichment_id': similar_enrichment.id,
                        'similarity_score': similarity_score,
                        'reason': f"Similar quality level ({enrichment.quality_level.value})",
                        'type': 'similar_quality'
                    })
        
        # Sort by similarity score and remove duplicates
        seen_ids = set()
        unique_similar = []
        for item in sorted(similar_content, key=lambda x: x['similarity_score'], reverse=True):
            if item['enrichment_id'] not in seen_ids:
                unique_similar.append(item)
                seen_ids.add(item['enrichment_id'])
        
        return unique_similar
    
    async def _calculate_content_similarity(self, enrichment1: ContentEnrichment, enrichment2: ContentEnrichment) -> float:
        """Calculate similarity between two content enrichments."""
        similarity_factors = []
        
        # Content type similarity
        if enrichment1.content_type == enrichment2.content_type:
            similarity_factors.append(1.0)
        else:
            similarity_factors.append(0.0)
        
        # Quality level similarity
        if enrichment1.quality_level == enrichment2.quality_level:
            similarity_factors.append(1.0)
        elif enrichment1.quality_level and enrichment2.quality_level:
            # Calculate quality level distance
            quality_levels = [QualityLevel.POOR, QualityLevel.AVERAGE, QualityLevel.GOOD, QualityLevel.EXCELLENT]
            try:
                idx1 = quality_levels.index(enrichment1.quality_level)
                idx2 = quality_levels.index(enrichment2.quality_level)
                distance = abs(idx1 - idx2)
                similarity_factors.append(1.0 - (distance / len(quality_levels)))
            except ValueError:
                similarity_factors.append(0.5)
        else:
            similarity_factors.append(0.5)
        
        # Language similarity
        if enrichment1.language == enrichment2.language:
            similarity_factors.append(1.0)
        else:
            similarity_factors.append(0.0)
        
        # Word count similarity
        if enrichment1.word_count and enrichment2.word_count:
            word_count_diff = abs(enrichment1.word_count - enrichment2.word_count)
            max_word_count = max(enrichment1.word_count, enrichment2.word_count)
            if max_word_count > 0:
                word_similarity = 1.0 - (word_count_diff / max_word_count)
                similarity_factors.append(word_similarity)
            else:
                similarity_factors.append(0.0)
        else:
            similarity_factors.append(0.5)
        
        return sum(similarity_factors) / len(similarity_factors)
    
    async def record_content_view(self, content_enrichment_id: UUID, user_id: Optional[UUID] = None):
        """Record a content view."""
        analytics = await self._get_analytics_by_content(content_enrichment_id)
        if not analytics:
            # Create analytics if it doesn't exist
            analytics = await self.create_content_analytics(content_enrichment_id)
        
        analytics.view_count += 1
        analytics.last_accessed = datetime.utcnow()
        
        await self.db.commit()
        
        # Update trends
        await self._update_usage_trend(analytics)
    
    async def record_content_download(self, content_enrichment_id: UUID, user_id: Optional[UUID] = None):
        """Record a content download."""
        analytics = await self._get_analytics_by_content(content_enrichment_id)
        if not analytics:
            analytics = await self.create_content_analytics(content_enrichment_id)
        
        analytics.download_count += 1
        analytics.last_accessed = datetime.utcnow()
        
        await self.db.commit()
        
        # Update trends
        await self._update_usage_trend(analytics)
    
    async def record_content_share(self, content_enrichment_id: UUID, user_id: Optional[UUID] = None):
        """Record a content share."""
        analytics = await self._get_analytics_by_content(content_enrichment_id)
        if not analytics:
            analytics = await self.create_content_analytics(content_enrichment_id)
        
        analytics.share_count += 1
        analytics.last_accessed = datetime.utcnow()
        
        await self.db.commit()
        
        # Update trends
        await self._update_usage_trend(analytics)
    
    async def _get_analytics_by_content(self, content_id: UUID) -> Optional[ContentAnalytics]:
        """Get analytics by content enrichment ID."""
        result = await self.db.execute(
            select(ContentAnalytics).where(ContentAnalytics.content_id == content_id)
        )
        return result.scalar_one_or_none()
    
    async def _update_usage_trend(self, analytics: ContentAnalytics):
        """Update usage trend with new data point."""
        # Find usage trend
        result = await self.db.execute(
            select(ContentTrend)
            .where(
                and_(
                    ContentTrend.analytics_id == analytics.id,
                    ContentTrend.trend_type == "usage"
                )
            )
        )
        usage_trend = result.scalar_one_or_none()
        
        if usage_trend:
            # Add new data point
            new_data_point = {
                "timestamp": time.time(),
                "value": analytics.view_count
            }
            
            if usage_trend.time_series_data:
                usage_trend.time_series_data.append(new_data_point)
                # Keep only last 30 data points
                if len(usage_trend.time_series_data) > 30:
                    usage_trend.time_series_data = usage_trend.time_series_data[-30:]
            else:
                usage_trend.time_series_data = [new_data_point]
            
            # Update trend value and direction
            usage_trend.trend_value = analytics.view_count
            
            # Calculate trend direction
            if len(usage_trend.time_series_data) >= 2:
                recent_values = usage_trend.time_series_data[-5:]  # Last 5 values
                if len(recent_values) >= 2:
                    first_value = recent_values[0]["value"]
                    last_value = recent_values[-1]["value"]
                    
                    if last_value > first_value * 1.1:
                        usage_trend.trend_direction = "increasing"
                    elif last_value < first_value * 0.9:
                        usage_trend.trend_direction = "decreasing"
                    else:
                        usage_trend.trend_direction = "stable"
            
            await self.db.commit()
    
    async def get_content_trends(self, content_enrichment_id: UUID, trend_type: str = None) -> List[ContentTrend]:
        """Get trends for specific content."""
        analytics = await self._get_analytics_by_content(content_enrichment_id)
        if not analytics:
            return []
        
        query = select(ContentTrend).where(ContentTrend.analytics_id == analytics.id)
        if trend_type:
            query = query.where(ContentTrend.trend_type == trend_type)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_content_recommendations(self, content_enrichment_id: UUID, limit: int = 10) -> List[ContentRecommendation]:
        """Get content recommendations for specific content."""
        analytics = await self._get_analytics_by_content(content_enrichment_id)
        if not analytics:
            return []
        
        result = await self.db.execute(
            select(ContentRecommendation)
            .options(selectinload(ContentRecommendation.recommended_content))
            .where(ContentRecommendation.analytics_id == analytics.id)
            .order_by(desc(ContentRecommendation.recommendation_score))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_trending_content(self, period: str = "daily", limit: int = 20) -> List[Dict[str, Any]]:
        """Get trending content based on usage patterns."""
        # Get content with highest view counts in recent period
        result = await self.db.execute(
            select(ContentAnalytics)
            .options(selectinload(ContentAnalytics.content))
            .order_by(desc(ContentAnalytics.view_count))
            .limit(limit)
        )
        
        trending_content = []
        for analytics in result.scalars().all():
            if analytics.content:
                trending_content.append({
                    "content_id": analytics.content_id,
                    "title": analytics.content.artifact.title if analytics.content.artifact else "Unknown",
                    "view_count": analytics.view_count,
                    "download_count": analytics.download_count,
                    "impact_score": analytics.impact_score,
                    "content_type": analytics.content.content_type.value,
                    "quality_level": analytics.content.quality_level.value if analytics.content.quality_level else None
                })
        
        return trending_content
    
    async def get_content_analytics_summary(self) -> Dict[str, Any]:
        """Get overall content analytics summary."""
        # Get total counts
        total_content = await self.db.execute(select(func.count(ContentEnrichment.id)))
        total_views = await self.db.execute(select(func.sum(ContentAnalytics.view_count)))
        total_downloads = await self.db.execute(select(func.sum(ContentAnalytics.download_count)))
        
        # Get content by type
        content_by_type = await self.db.execute(
            select(ContentEnrichment.content_type, func.count(ContentEnrichment.id))
            .group_by(ContentEnrichment.content_type)
        )
        
        # Get content by quality
        content_by_quality = await self.db.execute(
            select(ContentEnrichment.quality_level, func.count(ContentEnrichment.id))
            .group_by(ContentEnrichment.quality_level)
        )
        
        return {
            "total_content": total_content.scalar() or 0,
            "total_views": total_views.scalar() or 0,
            "total_downloads": total_downloads.scalar() or 0,
            "content_by_type": dict(content_by_type.all()),
            "content_by_quality": dict(content_by_quality.all()),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def update_recommendation_click(self, recommendation_id: UUID):
        """Record a recommendation click."""
        result = await self.db.execute(
            select(ContentRecommendation).where(ContentRecommendation.id == recommendation_id)
        )
        recommendation = result.scalar_one_or_none()
        
        if recommendation:
            recommendation.is_clicked = True
            recommendation.click_timestamp = datetime.utcnow()
            await self.db.commit()
