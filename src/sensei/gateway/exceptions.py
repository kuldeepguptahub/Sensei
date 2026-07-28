"""
Gateway exception hierarchy for Sensei.

All gateway-related exceptions inherit from GatewayError.
"""

class GatewayError(Exception):
    """Base class for all gateway exceptions."""
    pass


class GatewayConnectionError(GatewayError):
    """Raised when there's a connection problem with the gateway."""
    pass


class GatewayAuthenticationError(GatewayError):
    """Raised when authentication with the gateway fails."""
    pass


class GatewayTimeoutError(GatewayError):
    """Raised when the gateway request times out."""
    pass


class GatewayRateLimitError(GatewayError):
    """Raised when the gateway rate limit is exceeded."""
    pass


class GatewayResponseError(GatewayError):
    """Raised when the gateway returns an invalid or unexpected response."""
    pass