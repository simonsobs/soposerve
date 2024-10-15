"""
A simple python wrapper for the HTTP for SOPO.

API key can be stored in the SOPO_API_KEY environment variable.
Host can be stored in the SOPO_HOST environment variable.
"""

__all__ = [
    "Client",
    "collections",
    "product",
    "relationships",
]

from . import collections, product, relationships
from .core import Client
