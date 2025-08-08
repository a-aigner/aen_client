"""
hen_client – Aeneis API v2 Python wrapper.

Typical usage:
    from hen_client import HenClient

    client = HenClient(
        base_url="http://localhost:23000/api/v2",
        username="user",
        password="pass",
    )
    client.login()
    # ... use the API ...
    client.logout()
"""

from .manager import AenClient
from .exceptions import (
    AenClientError,
    AuthenticationError,
    PermissionDenied,
    NotFoundError,
    ValidationError,
    ConflictError,
    TransactionError,
    ServerError,
)
from .types import (
    View,
    AenLocalizedValue,
    AenCategory,
    AenProperty,
    AenObject,
    AenFile,
    QueryResult,
    SearchHit,
    JSON,
)

__all__ = [
    "AenClient",
    # Exceptions
    "AenClientError",
    "AuthenticationError",
    "PermissionDenied",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "TransactionError",
    "ServerError",
    # Types
    "View",
    "AenLocalizedValue",
    "AenCategory",
    "AenProperty",
    "AenObject",
    "AenFile",
    "QueryResult",
    "SearchHit",
    "JSON",
]

# Package version
try:
    from importlib.metadata import version, PackageNotFoundError  # Python 3.8+
except Exception:  # pragma: no cover
    version = None  # type: ignore
    PackageNotFoundError = Exception  # type: ignore

__version__ = "0.1.0"
if version is not None:
    try:
        __version__ = version("hen-client")  # If installed as a package
    except PackageNotFoundError:  # pragma: no cover
        pass
