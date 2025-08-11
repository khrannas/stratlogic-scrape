"""
Search API routes for the StratLogic Scraping System.

This module provides endpoints for advanced search functionality including
full-text search, semantic search, and content indexing.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...auth.jwt import get_current_user
from ...core.models import User
from ...services.search_service import SearchService, get_search_service

router = APIRouter(prefix="/search", tags=["search"])


# Pydantic models for API requests/responses
class SearchRequest(BaseModel):
    """Request model for search operations."""
    query: str
    search_type: str = "full_text"  # full_text, semantic, hybrid
    limit: int = 20
    offset: int = 0
    filters: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    """Response model for search results."""
    artifact_id: str
    title: str
    description: Optional[str]
    keywords: List[str]
    tags: List[str]
    score: float
    score_type: str  # rank, similarity, hybrid_score


class SearchResponse(BaseModel):
    """Response model for search operations."""
    results: List[SearchResult]
    total_count: int
    query: str
    search_type: str
    processing_time_ms: Optional[float]


class IndexRequest(BaseModel):
    """Request model for indexing operations."""
    artifact_id: UUID


class IndexResponse(BaseModel):
    """Response model for indexing operations."""
    success: bool
    message: str
    artifact_id: str


@router.post("/", response_model=SearchResponse)
async def search_content(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service)
) -> SearchResponse:
    """
    Search content using full-text, semantic, or hybrid search.
    
    This endpoint allows users to search through their artifacts using
    different search algorithms and provides ranked results.
    """
    try:
        if search_request.search_type == "full_text":
            results, total_count = await search_service.full_text_search(
                query=search_request.query,
                user_id=current_user.id,
                limit=search_request.limit,
                offset=search_request.offset,
                filters=search_request.filters
            )
        elif search_request.search_type == "semantic":
            results, total_count = await search_service.semantic_search(
                query=search_request.query,
                user_id=current_user.id,
                limit=search_request.limit,
                offset=search_request.offset,
                filters=search_request.filters
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid search type")
        
        # Convert results to response format
        search_results = []
        for result in results:
            score_type = "rank" if "rank" in result else "similarity"
            score = result.get("rank", result.get("similarity", 0.0))
            
            search_results.append(SearchResult(
                artifact_id=result["artifact_id"],
                title=result["title"],
                description=result["description"],
                keywords=result["keywords"],
                tags=result["tags"],
                score=score,
                score_type=score_type
            ))
        
        return SearchResponse(
            results=search_results,
            total_count=total_count,
            query=search_request.query,
            search_type=search_request.search_type,
            processing_time_ms=None  # Could be added to service response
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/index", response_model=IndexResponse)
async def index_artifact(
    index_request: IndexRequest,
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service)
) -> IndexResponse:
    """
    Index an artifact for search.
    
    This endpoint indexes an artifact for both full-text and semantic search,
    making it available for future search operations.
    """
    try:
        success = await search_service.index_artifact_for_search(index_request.artifact_id)
        
        if success:
            return IndexResponse(
                success=True,
                message="Artifact indexed successfully",
                artifact_id=str(index_request.artifact_id)
            )
        else:
            return IndexResponse(
                success=False,
                message="Failed to index artifact - no content found",
                artifact_id=str(index_request.artifact_id)
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.get("/full-text", response_model=SearchResponse)
async def full_text_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service)
) -> SearchResponse:
    """
    Perform full-text search using PostgreSQL.
    
    This endpoint uses PostgreSQL's built-in full-text search capabilities
    to find relevant artifacts based on text content.
    """
    try:
        results, total_count = await search_service.full_text_search(
            query=query,
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                artifact_id=result["artifact_id"],
                title=result["title"],
                description=result["description"],
                keywords=result["keywords"],
                tags=result["tags"],
                score=result["rank"],
                score_type="rank"
            ))
        
        return SearchResponse(
            results=search_results,
            total_count=total_count,
            query=query,
            search_type="full_text",
            processing_time_ms=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Full-text search failed: {str(e)}")


@router.get("/semantic", response_model=SearchResponse)
async def semantic_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service)
) -> SearchResponse:
    """
    Perform semantic search using sentence transformers.
    
    This endpoint uses AI-powered semantic search to find artifacts
    based on meaning rather than exact text matches.
    """
    try:
        results, total_count = await search_service.semantic_search(
            query=query,
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                artifact_id=result["artifact_id"],
                title=result["title"],
                description=result["description"],
                keywords=result["keywords"],
                tags=result["tags"],
                score=result["similarity"],
                score_type="similarity"
            ))
        
        return SearchResponse(
            results=search_results,
            total_count=total_count,
            query=query,
            search_type="semantic",
            processing_time_ms=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., description="Partial search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions"),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service)
) -> Dict[str, Any]:
    """
    Get search suggestions based on partial query.
    
    This endpoint provides search suggestions to help users
    formulate better search queries.
    """
    try:
        # Simple implementation - can be enhanced with more sophisticated suggestions
        suggestions = [
            f"{query} analysis",
            f"{query} research",
            f"{query} study",
            f"{query} report",
            f"{query} data"
        ]
        
        return {
            "query": query,
            "suggestions": suggestions[:limit],
            "total_suggestions": len(suggestions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.get("/stats")
async def get_search_stats(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service)
) -> Dict[str, Any]:
    """
    Get search statistics for the current user.
    
    This endpoint provides analytics about the user's search activity
    including search frequency, types, and performance metrics.
    """
    try:
        # This would be implemented in the search service
        # For now, return placeholder data
        return {
            "total_searches": 0,
            "search_types": {
                "full_text": 0,
                "semantic": 0
            },
            "avg_processing_time_ms": 0,
            "total_results": 0,
            "avg_results_per_search": 0,
            "period_days": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search stats: {str(e)}")
