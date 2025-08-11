"""
Search service for the StratLogic Scraping System.
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

import numpy as np
from sentence_transformers import SentenceTransformer, util
from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.models import Artifact
from ..core.models.search import (
    AnalysisType, ContentAnalysis, SearchEmbedding, SearchIndex, SearchQuery, SearchType
)
from ..core.config import get_settings


class SearchService:
    """Service for advanced search and content analysis."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self._sentence_model = None
    
    @property
    def sentence_model(self) -> SentenceTransformer:
        """Lazy load sentence transformer model."""
        if self._sentence_model is None:
            self._sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        return self._sentence_model
    
    async def index_artifact_for_search(self, artifact_id: UUID) -> bool:
        """Index an artifact for both full-text and semantic search."""
        try:
            query = select(Artifact).where(Artifact.id == artifact_id)
            result = await self.db.execute(query)
            artifact = result.scalar_one_or_none()
            
            if not artifact or not artifact.content_text:
                return False
            
            await self._create_full_text_index(artifact)
            await self._create_semantic_embedding(artifact)
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Failed to index artifact: {str(e)}")
    
    async def _create_full_text_index(self, artifact: Artifact) -> None:
        """Create full-text search index for an artifact."""
        content_parts = []
        if artifact.title:
            content_parts.append(artifact.title)
        if artifact.description:
            content_parts.append(artifact.description)
        if artifact.content_text:
            content_parts.append(artifact.content_text)
        
        content_text = " ".join(content_parts)
        
        search_vector_query = text("""
            to_tsvector('english', :content) || 
            to_tsvector('english', :title) || 
            to_tsvector('english', :description)
        """)
        
        result = await self.db.execute(
            search_vector_query,
            {
                "content": content_text,
                "title": artifact.title or "",
                "description": artifact.description or ""
            }
        )
        search_vector = result.scalar()
        
        existing_query = select(SearchIndex).where(SearchIndex.artifact_id == artifact.id)
        existing_result = await self.db.execute(existing_query)
        existing_index = existing_result.scalar_one_or_none()
        
        if existing_index:
            existing_index.content_text = content_text
            existing_index.search_vector = search_vector
            existing_index.title = artifact.title
            existing_index.description = artifact.description
            existing_index.keywords = json.dumps(artifact.keywords) if artifact.keywords else None
            existing_index.tags = json.dumps(artifact.tags) if artifact.tags else None
        else:
            search_index = SearchIndex(
                artifact_id=artifact.id,
                content_text=content_text,
                search_vector=search_vector,
                title=artifact.title,
                description=artifact.description,
                keywords=json.dumps(artifact.keywords) if artifact.keywords else None,
                tags=json.dumps(artifact.tags) if artifact.tags else None,
                language=artifact.language or "en"
            )
            self.db.add(search_index)
    
    async def _create_semantic_embedding(self, artifact: Artifact) -> None:
        """Create semantic search embedding for an artifact."""
        content_parts = []
        if artifact.title:
            content_parts.append(artifact.title)
        if artifact.description:
            content_parts.append(artifact.description)
        if artifact.content_text:
            content_parts.append(artifact.content_text[:2000])
        
        content_text = " ".join(content_parts)
        content_hash = hashlib.sha256(content_text.encode()).hexdigest()
        
        existing_query = select(SearchEmbedding).where(
            and_(
                SearchEmbedding.artifact_id == artifact.id,
                SearchEmbedding.model_name == self.sentence_model.get_sentence_embedding_dimension(),
                SearchEmbedding.content_hash == content_hash
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_embedding = existing_result.scalar_one_or_none()
        
        if existing_embedding:
            return
        
        embedding = self.sentence_model.encode(content_text)
        embedding_list = embedding.tolist()
        
        search_embedding = SearchEmbedding(
            artifact_id=artifact.id,
            model_name=self.sentence_model.get_sentence_embedding_dimension(),
            embedding_vector=json.dumps(embedding_list),
            content_hash=content_hash
        )
        self.db.add(search_embedding)
    
    async def full_text_search(
        self,
        query: str,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Perform full-text search using PostgreSQL."""
        start_time = time.time()
        
        search_query = text("""
            SELECT 
                si.artifact_id,
                si.title,
                si.description,
                si.keywords,
                si.tags,
                ts_rank(si.search_vector, plainto_tsquery('english', :query)) as rank
            FROM search_index si
            JOIN artifacts a ON si.artifact_id = a.id
            WHERE 
                si.is_active = 1
                AND a.user_id = :user_id
                AND si.search_vector @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT :limit OFFSET :offset
        """)
        
        result = await self.db.execute(
            search_query,
            {
                "query": query,
                "user_id": user_id,
                "limit": limit,
                "offset": offset
            }
        )
        
        rows = result.fetchall()
        results = []
        for row in rows:
            results.append({
                "artifact_id": str(row.artifact_id),
                "title": row.title,
                "description": row.description,
                "keywords": json.loads(row.keywords) if row.keywords else [],
                "tags": json.loads(row.tags) if row.tags else [],
                "rank": float(row.rank)
            })
        
        count_query = text("""
            SELECT COUNT(*) as total
            FROM search_index si
            JOIN artifacts a ON si.artifact_id = a.id
            WHERE 
                si.is_active = 1
                AND a.user_id = :user_id
                AND si.search_vector @@ plainto_tsquery('english', :query)
        """)
        
        count_result = await self.db.execute(
            count_query,
            {"query": query, "user_id": user_id}
        )
        total_count = count_result.scalar()
        
        processing_time = (time.time() - start_time) * 1000
        await self._record_search_query(
            user_id=user_id,
            query_text=query,
            search_type=SearchType.FULL_TEXT,
            filters=filters,
            results_count=len(results),
            processing_time_ms=processing_time
        )
        
        return results, total_count
    
    async def semantic_search(
        self,
        query: str,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Perform semantic search using sentence transformers."""
        start_time = time.time()
        
        query_embedding = self.sentence_model.encode(query)
        
        embeddings_query = select(SearchEmbedding).join(Artifact).where(
            and_(
                SearchEmbedding.is_active == 1,
                Artifact.user_id == user_id,
                SearchEmbedding.model_name == self.sentence_model.get_sentence_embedding_dimension()
            )
        )
        embeddings_result = await self.db.execute(embeddings_query)
        embeddings = embeddings_result.scalars().all()
        
        if not embeddings:
            return [], 0
        
        similarities = []
        for embedding in embeddings:
            embedding_vector = np.array(json.loads(embedding.embedding_vector))
            similarity = util.cos_sim(query_embedding, embedding_vector).item()
            similarities.append((embedding, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        paginated_similarities = similarities[offset:offset + limit]
        
        results = []
        for embedding, similarity in paginated_similarities:
            artifact_query = select(Artifact).where(Artifact.id == embedding.artifact_id)
            artifact_result = await self.db.execute(artifact_query)
            artifact = artifact_result.scalar_one_or_none()
            
            if artifact:
                results.append({
                    "artifact_id": str(artifact.id),
                    "title": artifact.title,
                    "description": artifact.description,
                    "keywords": artifact.keywords or [],
                    "tags": artifact.tags or [],
                    "similarity": float(similarity)
                })
        
        processing_time = (time.time() - start_time) * 1000
        await self._record_search_query(
            user_id=user_id,
            query_text=query,
            search_type=SearchType.SEMANTIC,
            filters=filters,
            results_count=len(results),
            processing_time_ms=processing_time
        )
        
        return results, len(similarities)
    
    async def _record_search_query(
        self,
        user_id: UUID,
        query_text: str,
        search_type: SearchType,
        filters: Optional[Dict[str, Any]] = None,
        results_count: int = 0,
        processing_time_ms: Optional[float] = None
    ) -> None:
        """Record search query for analytics."""
        search_query = SearchQuery(
            user_id=user_id,
            query_text=query_text,
            search_type=search_type,
            filters=json.dumps(filters) if filters else None,
            results_count=results_count,
            processing_time_ms=processing_time_ms
        )
        self.db.add(search_query)
        await self.db.commit()


async def get_search_service(db: AsyncSession) -> SearchService:
    """Dependency injection for search service."""
    return SearchService(db)
