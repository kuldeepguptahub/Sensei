"""
Gateway package for Sensei.

This package provides the interface to external LLM providers.
"""

from .client import generate
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
    'GatewayError',
    'GatewayConnectionError',
    'GatewayAuthenticationError',
    'GatewayTimeoutError',
    'GatewayRateLimitError',
    'GatewayResponseError'
]