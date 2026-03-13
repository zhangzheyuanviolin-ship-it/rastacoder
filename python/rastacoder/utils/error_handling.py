"""
Error Handling Utilities

Comprehensive error handling utilities for robust error management,
retry logic, and user-friendly error messages.
"""

import time
import random
import logging
from typing import Optional, Dict, Any, List, Callable, TypeVar, Union
from functools import wraps
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"  # Minor issue, can continue
    MEDIUM = "medium"  # Significant issue, retry recommended
    HIGH = "high"  # Serious issue, user action needed
    CRITICAL = "critical"  # App-breaking error


class ErrorType(Enum):
    """Error type categories."""
    NETWORK = "network"
    API = "api"
    FILE_SYSTEM = "file_system"
    PERMISSION = "permission"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    INTERNAL = "internal"
    USER = "user"


@dataclass
class NavixError:
    """
    Standardized error structure for NavixMind.
    
    Attributes:
        message: User-friendly error message
        error_type: Category of error
        severity: How serious the error is
        details: Additional technical details
        recoverable: Whether the error can be recovered from
        suggested_action: What the user should do
    """
    message: str
    error_type: ErrorType
    severity: ErrorSeverity
    details: Optional[Dict[str, Any]] = None
    recoverable: bool = True
    suggested_action: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "message": self.message,
            "error_type": self.error_type.value,
            "severity": self.severity.value,
            "details": self.details,
            "recoverable": self.recoverable,
            "suggested_action": self.suggested_action,
            "timestamp": time.time()
        }
    
    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.message}"


# Pre-defined error templates
ERROR_TEMPLATES = {
    "network_offline": NavixError(
        message="No internet connection. Please check your network and try again.",
        error_type=ErrorType.NETWORK,
        severity=ErrorSeverity.MEDIUM,
        suggested_action="Check your WiFi or mobile data connection"
    ),
    "api_rate_limit": NavixError(
        message="Too many requests. Please wait {seconds} seconds.",
        error_type=ErrorType.API,
        severity=ErrorSeverity.MEDIUM,
        recoverable=True,
        suggested_action="Wait before trying again"
    ),
    "api_quota_exceeded": NavixError(
        message="Daily API limit reached. Resets at midnight.",
        error_type=ErrorType.API,
        severity=ErrorSeverity.HIGH,
        recoverable=False,
        suggested_action="Upgrade your plan or wait until tomorrow"
    ),
    "file_not_found": NavixError(
        message="File not found: {path}",
        error_type=ErrorType.FILE_SYSTEM,
        severity=ErrorSeverity.MEDIUM,
        suggested_action="Check the file path and try again"
    ),
    "storage_full": NavixError(
        message="Device storage full ({used}/{total}). Free up space to continue.",
        error_type=ErrorType.RESOURCE,
        severity=ErrorSeverity.HIGH,
        recoverable=False,
        suggested_action="Delete unused files or apps to free up space"
    ),
    "permission_denied": NavixError(
        message="Permission denied: {permission}",
        error_type=ErrorType.PERMISSION,
        severity=ErrorSeverity.HIGH,
        recoverable=False,
        suggested_action="Grant the required permission in Settings"
    ),
    "timeout": NavixError(
        message="Operation timed out after {seconds}s",
        error_type=ErrorType.TIMEOUT,
        severity=ErrorSeverity.MEDIUM,
        recoverable=True,
        suggested_action="Try again or increase the timeout limit"
    ),
    "model_load_failed": NavixError(
        message="Failed to load AI model: {model}",
        error_type=ErrorType.RESOURCE,
        severity=ErrorSeverity.HIGH,
        suggested_action="Try a smaller model or free up memory"
    ),
    "invalid_input": NavixError(
        message="Invalid input: {reason}",
        error_type=ErrorType.VALIDATION,
        severity=ErrorSeverity.LOW,
        suggested_action="Check your input and try again"
    ),
    "internal_error": NavixError(
        message="An internal error occurred. The app will recover automatically.",
        error_type=ErrorType.INTERNAL,
        severity=ErrorSeverity.CRITICAL,
        recoverable=True,
        suggested_action="Restart the app if the problem persists"
    ),
}


def get_error_template(template_name: str, **kwargs) -> NavixError:
    """
    Get a pre-defined error template with formatted values.
    
    Args:
        template_name: Name of error template
        **kwargs: Values to format in the message
        
    Returns:
        NavixError with formatted message
    """
    template = ERROR_TEMPLATES.get(template_name, ERROR_TEMPLATES["internal_error"])
    
    if kwargs:
        message = template.message.format(**kwargs)
        details = {**template.details, **kwargs} if template.details else kwargs
        return NavixError(
            message=message,
            error_type=template.error_type,
            severity=template.severity,
            details=details,
            recoverable=template.recoverable,
            suggested_action=template.suggested_action
        )
    
    return template


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[List[type]] = None
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [Exception]
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add ±25% jitter to prevent thundering herd
            delay = delay * (0.75 + random.random() * 0.5)
        
        return delay


T = TypeVar('T')


def retry_with_config(config: RetryConfig):
    """
    Decorator for retrying functions with configurable behavior.
    
    Args:
        config: Retry configuration
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if exception is retryable
                    if not any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions):
                        raise
                    
                    # Don't retry on last attempt
                    if attempt == config.max_retries:
                        raise
                    
                    # Calculate and apply delay
                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{config.max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True
):
    """
    Simple retry decorator with common parameters.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay (exponential backoff)
        jitter: Whether to add random jitter
        
    Example:
        @retry(max_retries=3, delay=1.0)
        def fetch_data():
            ...
    """
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=delay,
        exponential_base=backoff,
        jitter=jitter
    )
    return retry_with_config(config)


class ErrorHandler:
    """
    Centralized error handler for NavixMind.
    
    Provides consistent error handling, logging, and recovery.
    """
    
    def __init__(self):
        self.error_history: List[NavixError] = []
        self.max_history = 100
        self.listeners: List[Callable[[NavixError], None]] = []
    
    def handle(
        self,
        error: Union[Exception, NavixError],
        context: Optional[Dict[str, Any]] = None
    ) -> NavixError:
        """
        Handle an error and return standardized NavixError.
        
        Args:
            error: Exception or NavixError to handle
            context: Additional context about the error
            
        Returns:
            Standardized NavixError
        """
        navix_error = self._convert_to_navix_error(error, context)
        
        # Add to history
        self.error_history.append(navix_error)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        # Log error
        self._log_error(navix_error)
        
        # Notify listeners
        for listener in self.listeners:
            try:
                listener(navix_error)
            except Exception as e:
                logger.error(f"Error listener failed: {e}")
        
        return navix_error
    
    def _convert_to_navix_error(
        self,
        error: Union[Exception, NavixError],
        context: Optional[Dict[str, Any]]
    ) -> NavixError:
        """Convert any exception to NavixError."""
        if isinstance(error, NavixError):
            return error
        
        # Map common exceptions to templates
        error_msg = str(error)
        
        if "No network" in error_msg or "connection" in error_msg.lower():
            return get_error_template("network_offline")
        
        if "timeout" in error_msg.lower():
            return get_error_template("timeout", seconds=context.get("timeout", 30))
        
        if "not found" in error_msg.lower() or "ENOENT" in error_msg:
            return get_error_template("file_not_found", path=context.get("path", "unknown"))
        
        if "permission" in error_msg.lower() or "EACCES" in error_msg:
            return get_error_template("permission_denied", permission=context.get("permission", "unknown"))
        
        if "quota" in error_msg.lower() or "limit" in error_msg.lower():
            return get_error_template("api_quota_exceeded")
        
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            return get_error_template("api_rate_limit", seconds=60)
        
        # Default to internal error
        return NavixError(
            message=error_msg or "An unexpected error occurred",
            error_type=ErrorType.INTERNAL,
            severity=ErrorSeverity.MEDIUM,
            details={"exception_type": type(error).__name__, **(context or {})}
        )
    
    def _log_error(self, error: NavixError):
        """Log error with appropriate level."""
        log_data = error.to_dict()
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {log_data}")
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {log_data}")
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {log_data}")
        else:
            logger.info(f"Low severity error: {log_data}")
    
    def add_listener(self, callback: Callable[[NavixError], None]):
        """Add error listener for real-time error handling."""
        self.listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[NavixError], None]):
        """Remove error listener."""
        if callback in self.listeners:
            self.listeners.remove(callback)
    
    def get_recent_errors(self, limit: int = 10) -> List[NavixError]:
        """Get most recent errors."""
        return self.error_history[-limit:]
    
    def clear_history(self):
        """Clear error history."""
        self.error_history.clear()


# Global error handler instance
global_error_handler = ErrorHandler()


def handle_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for automatic error handling.
    
    Wraps function calls with standardized error handling.
    
    Example:
        @handle_errors
        def process_file(path: str):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise global_error_handler.handle(e)
    
    return wrapper


def safe_execute(
    func: Callable[..., T],
    *args,
    default: Optional[T] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
    **kwargs
) -> Optional[T]:
    """
    Execute function safely with error handling.
    
    Args:
        func: Function to execute
        *args: Arguments to pass to function
        default: Default value to return on error
        on_error: Optional callback for error handling
        **kwargs: Keyword arguments to pass to function
        
    Returns:
        Function result or default value
        
    Example:
        result = safe_execute(risky_operation, arg1, arg2, default=None)
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if on_error:
            on_error(e)
        logger.debug(f"Safe execute caught: {e}")
        return default


# Context manager for error handling
from contextlib import contextmanager


@contextmanager
def error_context(operation_name: str, on_error: Optional[Callable[[Exception], None]] = None):
    """
    Context manager for error handling with operation tracking.
    
    Args:
        operation_name: Name of the operation for logging
        on_error: Optional error callback
        
    Example:
        with error_context("file_processing"):
            process_file(path)
    """
    try:
        yield
    except Exception as e:
        logger.error(f"Error in {operation_name}: {e}")
        if on_error:
            on_error(e)
        raise


# User-friendly error messages
def get_user_message(error: NavixError, include_technical: bool = False) -> str:
    """
    Generate user-friendly error message.
    
    Args:
        error: NavixError to format
        include_technical: Whether to include technical details
        
    Returns:
        User-friendly message string
    """
    message = error.message
    
    if include_technical and error.details:
        details_str = ", ".join(f"{k}={v}" for k, v in error.details.items())
        message += f" [{details_str}]"
    
    if error.suggested_action:
        message += f"\n\n💡 Tip: {error.suggested_action}"
    
    return message
