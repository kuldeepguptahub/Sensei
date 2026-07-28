"""
Retry mechanism for gateway requests.

This module handles transient failures with exponential backoff.
"""
import time
import random
from typing import Callable, TypeVar, Any
from .exceptions import (
    GatewayError,
    GatewayConnectionError,
    GatewayTimeoutError,
    GatewayRateLimitError
)

T = TypeVar('T')

# Transient exceptions that should be retried
TRANSIENT_EXCEPTIONS = (
    GatewayConnectionError,
    GatewayTimeoutError,
    GatewayRateLimitError
)


def execute_with_retry(
    request_func: Callable[[], T],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.1
) -> T:
    """
    Execute a request function with retry logic for transient failures.

    Args:
        request_func: The function to execute
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for exponential backoff
        jitter: Random jitter to add to delay

    Returns:
        The result of the successful request

    Raises:
        GatewayError: If all attempts fail
    """
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            return request_func()
        except TRANSIENT_EXCEPTIONS as e:
            last_exception = e
            if attempt < max_attempts:
                # Calculate delay with exponential backoff and jitter
                delay = initial_delay * (backoff_factor ** (attempt - 1))
                delay = delay * (1 + random.uniform(-jitter, jitter))
                time.sleep(delay)
            continue
        except GatewayError as e:
            # Non-transient errors are raised immediately
            raise

    # If we get here, all attempts failed
    raise last_exception or GatewayError("All retry attempts failed")