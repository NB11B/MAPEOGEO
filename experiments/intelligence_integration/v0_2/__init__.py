"""MAPEOGEO to Intelligence Integration v0.2: Authority Assessment Extension.

Extends v0.1 read-only analytical adapter with actor-to-actor legal authority
evaluation while preserving pristine reference semantics and host immutability.
"""

from .authority_adapter import MAPEOGEOAuthorityAdapter

__all__ = ["MAPEOGEOAuthorityAdapter"]
