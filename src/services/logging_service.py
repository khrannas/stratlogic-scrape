"""
Logging service for the StratLogic Scraping System.

This module provides comprehensive logging functionality using structlog,
including structured logging, log aggregation, search capabilities,
and log level management.
"""

import logging
import sys
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional, List
from pathlib import Path

import structlog
from structlog.stdlib import LoggerFactory
from structlog.processors import (
    TimeStamper, JSONRenderer, StackInfoRenderer,
    format_exc_info, add_log_level, add_logger_name
)


class StructuredLogger:
    """Structured logger with advanced features."""
    
    def __init__(self, name: str, log_level: str = "INFO"):
        self.name = name
        self.log_level = log_level
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> structlog.stdlib.BoundLogger:
        """Setup structured logger with processors."""
        # Configure structlog
        structlog.configure(
            processors=[
                # Add timestamp
                TimeStamper(fmt="iso"),
                
                # Add log level and logger name
                add_log_level,
                add_logger_name,
                
                # Add stack info for exceptions
                StackInfoRenderer(),
                
                # Format exception info
                format_exc_info,
                
                # Render as JSON
                JSONRenderer()
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Get logger
        logger = structlog.get_logger(self.name)
        
        # Set log level
        logging.getLogger(self.name).setLevel(getattr(logging, self.log_level.upper()))
        
        return logger
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data."""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data."""
        self.logger.debug(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with structured data."""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with structured data."""
        self.logger.exception(message, **kwargs)


class LogAggregator:
    """Log aggregator for collecting and searching logs."""
    
    def __init__(self, log_file: str = "logs/app.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_buffer = []
        self.buffer_size = 1000
    
    def add_log_entry(self, log_entry: Dict[str, Any]):
        """Add log entry to buffer and flush if needed."""
        self.log_buffer.append(log_entry)
        
        if len(self.log_buffer) >= self.buffer_size:
            self.flush_buffer()
    
    def flush_buffer(self):
        """Flush log buffer to file."""
        if not self.log_buffer:
            return
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                for entry in self.log_buffer:
                    f.write(json.dumps(entry) + "\n")
            
            self.log_buffer.clear()
        except Exception as e:
            # Fallback to stderr if file writing fails
            sys.stderr.write(f"Log writing failed: {e}\n")
    
    def search_logs(self, 
                   query: str = None,
                   level: str = None,
                   start_time: datetime = None,
                   end_time: datetime = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        """Search logs with various filters."""
        results = []
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        log_entry = json.loads(line)
                        
                        # Apply filters
                        if not self._matches_filters(log_entry, query, level, start_time, end_time):
                            continue
                        
                        results.append(log_entry)
                        
                        if len(results) >= limit:
                            break
                            
                    except json.JSONDecodeError:
                        continue
                        
        except FileNotFoundError:
            pass
        
        return results
    
    def _matches_filters(self, 
                        log_entry: Dict[str, Any],
                        query: str = None,
                        level: str = None,
                        start_time: datetime = None,
                        end_time: datetime = None) -> bool:
        """Check if log entry matches all filters."""
        # Level filter
        if level and log_entry.get("level", "").upper() != level.upper():
            return False
        
        # Time filter
        if start_time or end_time:
            try:
                log_time = datetime.fromisoformat(log_entry.get("timestamp", "").replace("Z", "+00:00"))
                
                if start_time and log_time < start_time:
                    return False
                
                if end_time and log_time > end_time:
                    return False
                    
            except (ValueError, TypeError):
                return False
        
        # Query filter
        if query:
            log_text = json.dumps(log_entry).lower()
            if query.lower() not in log_text:
                return False
        
        return True
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get log statistics."""
        stats = {
            "total_entries": 0,
            "entries_by_level": {},
            "entries_by_hour": {},
            "buffer_size": len(self.log_buffer)
        }
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        log_entry = json.loads(line)
                        stats["total_entries"] += 1
                        
                        # Count by level
                        level = log_entry.get("level", "unknown")
                        stats["entries_by_level"][level] = stats["entries_by_level"].get(level, 0) + 1
                        
                        # Count by hour
                        try:
                            log_time = datetime.fromisoformat(log_entry.get("timestamp", "").replace("Z", "+00:00"))
                            hour = log_time.strftime("%Y-%m-%d %H:00")
                            stats["entries_by_hour"][hour] = stats["entries_by_hour"].get(hour, 0) + 1
                        except (ValueError, TypeError):
                            pass
                            
                    except json.JSONDecodeError:
                        continue
                        
        except FileNotFoundError:
            pass
        
        return stats


class LogLevelManager:
    """Manager for log level configuration."""
    
    def __init__(self):
        self.loggers = {}
        self.default_level = "INFO"
    
    def set_logger_level(self, logger_name: str, level: str):
        """Set log level for specific logger."""
        try:
            logger = logging.getLogger(logger_name)
            logger.setLevel(getattr(logging, level.upper()))
            self.loggers[logger_name] = level
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid log level: {level}")
    
    def get_logger_level(self, logger_name: str) -> str:
        """Get current log level for logger."""
        logger = logging.getLogger(logger_name)
        return logging.getLevelName(logger.level)
    
    def set_default_level(self, level: str):
        """Set default log level for all loggers."""
        self.default_level = level
        logging.getLogger().setLevel(getattr(logging, level.upper()))
    
    def get_all_loggers(self) -> Dict[str, str]:
        """Get all configured loggers and their levels."""
        return self.loggers.copy()


class DistributedTracing:
    """Distributed tracing for request tracking."""
    
    def __init__(self):
        self.trace_id = None
        self.span_id = None
        self.parent_span_id = None
    
    def start_trace(self, trace_id: str = None, parent_span_id: str = None):
        """Start a new trace."""
        import uuid
        self.trace_id = trace_id or str(uuid.uuid4())
        self.span_id = str(uuid.uuid4())
        self.parent_span_id = parent_span_id
    
    def get_trace_context(self) -> Dict[str, str]:
        """Get current trace context."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id
        }
    
    def add_trace_to_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add trace context to log data."""
        if self.trace_id:
            log_data.update(self.get_trace_context())
        return log_data


class MetricsCollector:
    """Collector for application metrics."""
    
    def __init__(self):
        self.metrics = {
            "request_count": 0,
            "error_count": 0,
            "response_times": [],
            "log_entries": 0
        }
    
    def record_request(self, response_time: float = None):
        """Record a request."""
        self.metrics["request_count"] += 1
        if response_time is not None:
            self.metrics["response_times"].append(response_time)
            # Keep only last 1000 response times
            if len(self.metrics["response_times"]) > 1000:
                self.metrics["response_times"] = self.metrics["response_times"][-1000:]
    
    def record_error(self):
        """Record an error."""
        self.metrics["error_count"] += 1
    
    def record_log_entry(self):
        """Record a log entry."""
        self.metrics["log_entries"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        metrics = self.metrics.copy()
        
        # Calculate average response time
        if metrics["response_times"]:
            metrics["avg_response_time"] = sum(metrics["response_times"]) / len(metrics["response_times"])
        else:
            metrics["avg_response_time"] = 0
        
        # Calculate error rate
        if metrics["request_count"] > 0:
            metrics["error_rate"] = metrics["error_count"] / metrics["request_count"]
        else:
            metrics["error_rate"] = 0
        
        return metrics
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.metrics = {
            "request_count": 0,
            "error_count": 0,
            "response_times": [],
            "log_entries": 0
        }


# Global instances
_log_aggregator = LogAggregator()
_log_level_manager = LogLevelManager()
_tracing = DistributedTracing()
_metrics_collector = MetricsCollector()


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


def get_log_aggregator() -> LogAggregator:
    """Get the global log aggregator instance."""
    return _log_aggregator


def get_log_level_manager() -> LogLevelManager:
    """Get the global log level manager instance."""
    return _log_level_manager


def get_tracing() -> DistributedTracing:
    """Get the global distributed tracing instance."""
    return _tracing


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics_collector


def setup_logging(config: Dict[str, Any] = None):
    """Setup logging configuration."""
    config = config or {}
    
    # Set default log level
    default_level = config.get("default_level", "INFO")
    _log_level_manager.set_default_level(default_level)
    
    # Configure specific loggers
    for logger_name, level in config.get("loggers", {}).items():
        _log_level_manager.set_logger_level(logger_name, level)
    
    # Setup file handler for root logger
    log_file = config.get("log_file", "logs/app.log")
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Add formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Add to root logger
    logging.getLogger().addHandler(file_handler)


def log_request(request_data: Dict[str, Any], response_data: Dict[str, Any] = None):
    """Log request and response data."""
    logger = get_logger("request")
    
    log_data = {
        "request": request_data,
        "response": response_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Add trace context
    log_data = _tracing.add_trace_to_log(log_data)
    
    logger.info("Request processed", **log_data)
    _log_aggregator.add_log_entry(log_data)
    _metrics_collector.record_request()


def log_error(error_data: Dict[str, Any]):
    """Log error data."""
    logger = get_logger("error")
    
    log_data = {
        "error": error_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Add trace context
    log_data = _tracing.add_trace_to_log(log_data)
    
    logger.error("Error occurred", **log_data)
    _log_aggregator.add_log_entry(log_data)
    _metrics_collector.record_error()


def log_performance(operation: str, duration: float, details: Dict[str, Any] = None):
    """Log performance metrics."""
    logger = get_logger("performance")
    
    log_data = {
        "operation": operation,
        "duration": duration,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Add trace context
    log_data = _tracing.add_trace_to_log(log_data)
    
    logger.info("Performance metric", **log_data)
    _log_aggregator.add_log_entry(log_data)
    _metrics_collector.record_request(duration)
