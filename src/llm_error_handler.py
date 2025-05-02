import logging
import time
import random
from typing import Optional, Dict, Any, List, Type
from dataclasses import dataclass
from enum import Enum
import backoff
from functools import wraps

class LLMErrorType(Enum):
    """Types of errors that can occur during LLM operations"""
    NETWORK = "network_error"
    TIMEOUT = "timeout_error"
    RATE_LIMIT = "rate_limit_error"
    AUTHENTICATION = "authentication_error"
    INVALID_REQUEST = "invalid_request_error"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown_error"

@dataclass
class LLMError:
    """Structured error information"""
    error_type: LLMErrorType
    message: str
    details: Dict[str, Any]
    retry_count: int = 0
    timestamp: float = 0.0

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open

    def record_failure(self):
        """Record a failure and update circuit breaker state"""
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "open"

    def record_success(self):
        """Record a success and reset circuit breaker"""
        self.failures = 0
        self.state = "closed"

    def can_execute(self) -> bool:
        """Check if operation can be executed based on circuit breaker state"""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if time.time() - self.last_failure_time >= self.reset_timeout:
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True

class LLMErrorHandler:
    """Comprehensive error handling for LLM operations"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.circuit_breaker = CircuitBreaker()
        self.error_stats: Dict[LLMErrorType, int] = {error_type: 0 for error_type in LLMErrorType}
    
    def _log_error(self, error: LLMError):
        """Log error with appropriate level and details"""
        self.error_stats[error.error_type] += 1
        error_msg = f"LLM Error: {error.error_type.value} - {error.message}"
        if error.error_type in [LLMErrorType.NETWORK, LLMErrorType.SERVER_ERROR]:
            self.logger.error(error_msg, extra=error.details)
        else:
            self.logger.warning(error_msg, extra=error.details)
    
    def _create_error(self, error_type: LLMErrorType, message: str, details: Dict[str, Any]) -> LLMError:
        """Create a structured error object"""
        return LLMError(
            error_type=error_type,
            message=message,
            details=details,
            timestamp=time.time()
        )
    
    def handle_error(self, error: LLMError) -> bool:
        """
        Handle an error and determine if retry should be attempted
        
        Args:
            error: The error to handle
            
        Returns:
            bool: True if retry should be attempted, False otherwise
        """
        self._log_error(error)
        
        if not self.circuit_breaker.can_execute():
            return False
        
        if error.error_type in [LLMErrorType.NETWORK, LLMErrorType.TIMEOUT, LLMErrorType.RATE_LIMIT]:
            self.circuit_breaker.record_failure()
            return True
        elif error.error_type in [LLMErrorType.AUTHENTICATION, LLMErrorType.INVALID_REQUEST]:
            return False
        else:
            self.circuit_breaker.record_failure()
            return False
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get statistics about encountered errors"""
        return {error_type.value: count for error_type, count in self.error_stats.items()}
    
    def reset_stats(self):
        """Reset error statistics"""
        self.error_stats = {error_type: 0 for error_type in LLMErrorType}
        self.circuit_breaker = CircuitBreaker()

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    jitter: bool = True
):
    """
    Decorator for retrying operations with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        jitter: Whether to add random jitter to delays
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt == max_retries:
                        raise
                    
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    if jitter:
                        delay *= random.uniform(0.5, 1.5)
                    
                    time.sleep(delay)
            raise last_error
        return wrapper
    return decorator 