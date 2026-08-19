"""
Gateway package for Sensei.

This package provides the interface to external LLM providers.
"""

from .client import generate, generate_stream
from .exceptions import (
    GatewayError,
    GatewayConnectionError,
    GatewayAuthenticationError,
    GatewayTimeoutError,
    GatewayRateLimitError,
    GatewayResponseError
)

__all__ = [
    'generate',
    'generate_stream',
    'GatewayError',
    'GatewayConnectionError',
    'GatewayAuthenticationError',
    'GatewayTimeoutError',
    'GatewayRateLimitError',
    'GatewayResponseError'
]