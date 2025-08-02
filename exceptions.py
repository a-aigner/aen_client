"""
Custom exceptions for hen_client.
"""


class AenClientError(Exception):
    """Base exception for all hen_client errors."""
    pass


class AuthenticationError(AenClientError):
    """Login failed, credentials missing/invalid, or session not established."""
    pass


class PermissionDenied(AenClientError):
    """Authenticated but not authorized (HTTP 403) or similar."""
    pass


class NotFoundError(AenClientError):
    """A requested resource does not exist (HTTP 404)."""
    pass


class ValidationError(AenClientError):
    """Client-side validation or API reported input errors (HTTP 400/405)."""
    pass


class ConflictError(AenClientError):
    """State conflict (e.g., concurrent update, open transaction) (HTTP 409)."""
    pass


class TransactionError(AenClientError):
    """Transaction lifecycle problems (commit/rollback without open tx, etc.)."""
    pass


class ServerError(AenClientError):
    """Unexpected server-side failure (HTTP 5xx)."""
    pass
