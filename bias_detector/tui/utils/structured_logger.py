"""
Structured logging for TUI application.

Provides enhanced logging with context, timestamps, and structured output.
"""

import logging
import json
import sys
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path


class StructuredLogger:
    """
    Enhanced logger with structured output for TUI applications.
    
    Features:
    - JSON-formatted logs for parsing
    - Context-aware logging
    - Performance timing
    - Error categorization
    - Component-specific log levels
    """

    def __init__(self, name: str, log_file: Optional[Path] = None):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            log_file: Optional log file path
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler disabled for TUI to avoid display interference
        # Logs go to file only when TUI is running
        if not log_file:
            # Create default log file if none provided
            log_file = Path("data/logs/tui.log")
            log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # File handler for detailed logs
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = StructuredFormatter(include_details=True)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str, component: str = "general", **context) -> None:
        """Log debug message with context."""
        self._log(logging.DEBUG, message, component, **context)

    def info(self, message: str, component: str = "general", **context) -> None:
        """Log info message with context."""
        self._log(logging.INFO, message, component, **context)

    def warning(self, message: str, component: str = "general", **context) -> None:
        """Log warning message with context."""
        self._log(logging.WARNING, message, component, **context)

    def error(self, message: str, component: str = "general", error: Optional[Exception] = None, **context) -> None:
        """Log error message with context and optional exception."""
        if error:
            context['error_type'] = type(error).__name__
            context['error_message'] = str(error)
            context['error_traceback'] = self._get_traceback(error)
        
        self._log(logging.ERROR, message, component, **context)

    def critical(self, message: str, component: str = "general", error: Optional[Exception] = None, **context) -> None:
        """Log critical message with context and optional exception."""
        if error:
            context['error_type'] = type(error).__name__
            context['error_message'] = str(error)
            context['error_traceback'] = self._get_traceback(error)
        
        self._log(logging.CRITICAL, message, component, **context)

    def performance(self, operation: str, duration_ms: float, component: str = "performance", **context) -> None:
        """Log performance timing."""
        context.update({
            'operation': operation,
            'duration_ms': duration_ms,
            'performance_type': 'timing'
        })
        self._log(logging.INFO, f"Performance: {operation} took {duration_ms:.2f}ms", component, **context)

    def user_action(self, action: str, component: str = "ui", **context) -> None:
        """Log user interaction."""
        context.update({
            'action': action,
            'interaction_type': 'user_action'
        })
        self._log(logging.INFO, f"User action: {action}", component, **context)

    def experiment_event(self, event_type: str, session_id: str, component: str = "experiment", **context) -> None:
        """Log experiment-related events."""
        context.update({
            'event_type': event_type,
            'session_id': session_id,
            'experiment_event': True
        })
        self._log(logging.INFO, f"Experiment event: {event_type} for session {session_id}", component, **context)

    def _log(self, level: int, message: str, component: str, **context) -> None:
        """Internal logging method with structured data."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': logging.getLevelName(level),
            'component': component,
            'message': message,
            'context': context
        }
        
        # Add extra data for formatter
        extra = {'structured_data': log_data}
        self.logger.log(level, message, extra=extra)

    def _get_traceback(self, error: Exception) -> Optional[str]:
        """Extract traceback from exception."""
        import traceback
        return traceback.format_exc() if error else None

    def start_timer(self, operation: str) -> 'PerformanceTimer':
        """Start a performance timer."""
        return PerformanceTimer(operation, self)


class PerformanceTimer:
    """Context manager for timing operations."""

    def __init__(self, operation: str, logger: StructuredLogger):
        self.operation = operation
        self.logger = logger
        self.start_time = None

    def __enter__(self):
        import time
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.logger.performance(self.operation, duration_ms)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured log output."""

    def __init__(self, include_details: bool = False):
        """
        Initialize formatter.
        
        Args:
            include_details: Whether to include full JSON details
        """
        super().__init__()
        self.include_details = include_details

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured data."""
        # Get structured data if available
        structured_data = getattr(record, 'structured_data', None)
        
        if self.include_details and structured_data:
            # Full JSON output for file logs
            return json.dumps(structured_data, default=str, ensure_ascii=False)
        elif structured_data:
            # Simplified console output
            timestamp = structured_data.get('timestamp', '')[:19]  # Remove microseconds and Z
            level = structured_data.get('level', 'INFO')
            component = structured_data.get('component', 'general')
            message = structured_data.get('message', '')
            
            # Add context indicators
            context = structured_data.get('context', {})
            context_str = ''
            
            if context.get('performance_type') == 'timing':
                operation = context.get('operation', 'unknown')
                duration = context.get('duration_ms', 0)
                context_str = f" [PERF: {operation} {duration:.1f}ms]"
            elif context.get('interaction_type') == 'user_action':
                action = context.get('action', 'unknown')
                context_str = f" [ACTION: {action}]"
            elif context.get('experiment_event'):
                event_type = context.get('event_type', 'unknown')
                session_id = context.get('session_id', 'unknown')
                context_str = f" [EXPERIMENT: {event_type} {session_id[:8]}...]"
            elif context.get('error_type'):
                error_type = context.get('error_type', 'Unknown')
                context_str = f" [ERROR: {error_type}]"
            
            return f"{timestamp} [{level:8}] {component:15} {message}{context_str}"
        else:
            # Fallback to standard formatting
            return f"{record.levelname}: {record.getMessage()}"


# Global logger instance
_tui_logger: Optional[StructuredLogger] = None


def get_logger(name: str = "bias_detector.tui", log_file: Optional[Path] = None) -> StructuredLogger:
    """
    Get or create structured logger instance.
    
    Args:
        name: Logger name
        log_file: Optional log file path
        
    Returns:
        StructuredLogger instance
    """
    global _tui_logger
    if _tui_logger is None:
        # Create default log file for TUI if none provided
        if log_file is None:
            log_file = Path("data/logs/tui.log")
            log_file.parent.mkdir(parents=True, exist_ok=True)
        _tui_logger = StructuredLogger(name, log_file)
    return _tui_logger


def log_performance(operation: str):
    """Decorator for logging function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger()
            with logger.start_timer(operation):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def log_user_action(action: str):
    """Decorator for logging user actions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger()
            logger.user_action(action)
            return func(*args, **kwargs)
        return wrapper
    return decorator