"""
Lightweight types mirroring common Aeneis API entities.

These are intentionally permissive to avoid over-constraining the wire format.
Use with `typing`-friendly tooling or switch to Pydantic models later if desired.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union


# ---- Common primitives -------------------------------------------------------

View = Literal["simple", "detailed", "all"]  # Used by many GET endpoints


# ---- Localized text ----------------------------------------------------------

@dataclass
class AenLocalizedValue:
    locale: Optional[str] = None
    value: Optional[str] = None


# ---- Categories / Properties / Objects --------------------------------------

@dataclass
class AenCategory:
    id: Optional[str] = None      # numeric/string id as returned by API
    guid: Optional[str] = None
    name: Optional[str] = None
    label: Optional[str] = None


@dataclass
class AenProperty:
    id: Optional[str] = None
    guid: Optional[str] = None
    name: Optional[str] = None
    label: Optional[str] = None
    type: Optional[str] = None    # e.g. "string", "double", "date", "long", "boolean", "object", "objects", "html"
    value: Optional[Any] = None   # actual value as delivered by API


@dataclass
class AenObject:
    id: str                       # object id (OID)
    guid: Optional[str] = None
    name: Optional[str] = None
    label: Optional[str] = None
    labels: Optional[List[AenLocalizedValue]] = None
    category: Optional[AenCategory] = None
    properties: Optional[List[AenProperty]] = None


# ---- Files attached to objects ----------------------------------------------

@dataclass
class AenFile:
    content: Optional[str] = None       # base64 or server-provided representation
    filename: Optional[str] = None
    position: Optional[int] = None
    attribute_name: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None


# ---- Search / Query shapes ---------------------------------------------------

class QueryResult(TypedDict, total=False):
    """
    Result shape for /object/{id}/query/{queryId} and /objects/query/{queryId}.
    Keys are optional to reflect varying server-side query definitions.
    """
    sourceObject: AenObject
    sourceAttribute: AenObject
    object: AenObject
    value: Union[str, int, float, bool]


class SearchHit(TypedDict, total=False):
    """
    Typical search hit payload; structure may vary by server configuration.
    """
    object: AenObject
    score: float
    highlight: Dict[str, List[str]]


# ---- Generic JSON mappings ---------------------------------------------------

JSON = Union[None, bool, int, float, str, List["JSON"], Dict[str, "JSON"]]


__all__ = [
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
