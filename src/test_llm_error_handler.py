import unittest
import time
import logging
from unittest.mock import patch, MagicMock
from llm_error_handler import (
    LLMErrorHandler,
    LLMError,
    LLMErrorType,
    CircuitBreaker,
    retry_with_backoff
)

class TestLLMErrorHandler(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.handler = LLMErrorHandler(logger=self.logger)
    
    def test_error_creation(self):
        """Test creation of error objects"""
        error = LLMError(
            error_type=LLMErrorType.NETWORK,
            message="Connection failed",
            details={"url": "http://example.com"}
        )
        self.assertEqual(error.error_type, LLMErrorType.NETWORK)
        self.assertEqual(error.message, "Connection failed")
        self.assertEqual(error.details["url"], "http://example.com")
    
    def test_error_handling(self):
        """Test error handling logic"""
        # Test retryable error
        error = LLMError(
            error_type=LLMErrorType.NETWORK,
            message="Connection failed",
            details={}
        )
        should_retry = self.handler.handle_error(error)
        self.assertTrue(should_retry)
        
        # Test non-retryable error
        error = LLMError(
            error_type=LLMErrorType.AUTHENTICATION,
            message="Invalid credentials",
            details={}
        )
        should_retry = self.handler.handle_error(error)
        self.assertFalse(should_retry)
    
    def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        breaker = CircuitBreaker(failure_threshold=2, reset_timeout=1)
        
        # Test normal operation
        self.assertTrue(breaker.can_execute())
        
        # Test failure threshold
        breaker.record_failure()
        self.assertTrue(breaker.can_execute())
        breaker.record_failure()
        self.assertFalse(breaker.can_execute())
        
        # Test reset timeout
        time.sleep(1.1)  # Wait for reset timeout
        self.assertTrue(breaker.can_execute())
        
        # Test success recording
        breaker.record_success()
        self.assertTrue(breaker.can_execute())
        self.assertEqual(breaker.failures, 0)
    
    def test_error_stats(self):
        """Test error statistics tracking"""
        # Record some errors
        self.handler.handle_error(LLMError(
            error_type=LLMErrorType.NETWORK,
            message="test",
            details={}
        ))
        self.handler.handle_error(LLMError(
            error_type=LLMErrorType.NETWORK,
            message="test",
            details={}
        ))
        self.handler.handle_error(LLMError(
            error_type=LLMErrorType.AUTHENTICATION,
            message="test",
            details={}
        ))
        
        # Check stats
        stats = self.handler.get_error_stats()
        self.assertEqual(stats["network_error"], 2)
        self.assertEqual(stats["authentication_error"], 1)
        
        # Test reset
        self.handler.reset_stats()
        stats = self.handler.get_error_stats()
        self.assertEqual(stats["network_error"], 0)
    
    def test_retry_decorator(self):
        """Test retry with backoff decorator"""
        @retry_with_backoff(max_retries=2, base_delay=0.1)
        def failing_function():
            raise Exception("Test error")
        
        start_time = time.time()
        with self.assertRaises(Exception):
            failing_function()
        duration = time.time() - start_time
        
        # Should have waited for two retries with exponential backoff
        # 0.1 + 0.2 = 0.3 seconds minimum
        self.assertGreaterEqual(duration, 0.3)
    
    def test_error_logging(self):
        """Test error logging"""
        with patch.object(self.logger, 'error') as mock_error:
            error = LLMError(
                error_type=LLMErrorType.NETWORK,
                message="Connection failed",
                details={"url": "http://example.com"}
            )
            self.handler.handle_error(error)
            mock_error.assert_called_once()
    
    def test_error_type_handling(self):
        """Test handling of different error types"""
        error_types = [
            (LLMErrorType.NETWORK, True),
            (LLMErrorType.TIMEOUT, True),
            (LLMErrorType.RATE_LIMIT, True),
            (LLMErrorType.AUTHENTICATION, False),
            (LLMErrorType.INVALID_REQUEST, False),
            (LLMErrorType.SERVER_ERROR, False),
            (LLMErrorType.UNKNOWN, False)
        ]
        
        for error_type, should_retry in error_types:
            error = LLMError(
                error_type=error_type,
                message="test",
                details={}
            )
            result = self.handler.handle_error(error)
            self.assertEqual(result, should_retry)

if __name__ == "__main__":
    unittest.main() 