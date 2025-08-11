"""
Performance optimization API routes for the StratLogic Scraping System.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...auth.jwt import get_current_user
from ...core.models import User
from ...services.performance_service import PerformanceService, get_performance_service

router = APIRouter(prefix="/performance", tags=["performance"])


class OptimizationResponse(BaseModel):
    """Response model for optimization operations."""
    success: bool
    message: str
    data: Dict[str, Any]


class PerformanceResponse(BaseModel):
    """Response model for performance monitoring."""
    database: Dict[str, Any]
    cache: Dict[str, Any]
    timestamp: str


@router.post("/optimize/database", response_model=OptimizationResponse)
async def optimize_database(
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceService = Depends(get_performance_service)
) -> OptimizationResponse:
    """
    Optimize database queries and performance.
    
    This endpoint analyzes slow queries and provides optimization recommendations.
    """
    try:
        result = await performance_service.optimize_database_queries()
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return OptimizationResponse(
            success=True,
            message="Database optimization completed successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database optimization failed: {str(e)}")


@router.post("/optimize/caching", response_model=OptimizationResponse)
async def optimize_caching(
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceService = Depends(get_performance_service)
) -> OptimizationResponse:
    """
    Implement caching strategy optimization.
    
    This endpoint sets up Redis caching and monitors cache performance.
    """
    try:
        result = await performance_service.implement_caching_strategy()
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return OptimizationResponse(
            success=True,
            message="Caching strategy implemented successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Caching optimization failed: {str(e)}")


@router.get("/monitor", response_model=PerformanceResponse)
async def monitor_performance(
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceService = Depends(get_performance_service)
) -> PerformanceResponse:
    """
    Monitor system performance metrics.
    
    This endpoint provides real-time performance monitoring including
    database performance, cache statistics, and system health.
    """
    try:
        result = await performance_service.monitor_performance()
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return PerformanceResponse(
            database=result["database"],
            cache=result["cache"],
            timestamp=result.get("timestamp", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance monitoring failed: {str(e)}")


@router.get("/stats")
async def get_performance_stats(
    current_user: User = Depends(get_current_user),
    performance_service: PerformanceService = Depends(get_performance_service)
) -> Dict[str, Any]:
    """
    Get detailed performance statistics.
    
    This endpoint provides comprehensive performance statistics
    for system monitoring and optimization.
    """
    try:
        # Get database optimization stats
        db_optimization = await performance_service.optimize_database_queries()
        
        # Get caching stats
        caching_stats = await performance_service.implement_caching_strategy()
        
        # Get monitoring stats
        monitoring_stats = await performance_service.monitor_performance()
        
        return {
            "database_optimization": db_optimization,
            "caching_strategy": caching_stats,
            "performance_monitoring": monitoring_stats,
            "summary": {
                "slow_queries_count": len(db_optimization.get("slow_queries", [])),
                "cache_implemented": caching_stats.get("cache_implemented", False),
                "total_queries": monitoring_stats.get("database", {}).get("total_queries", 0)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {str(e)}")
